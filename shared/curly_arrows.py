"""
Draw curly (electron-pushing) arrows for a mechanism vector [code, i, j, k, l]
as produced by shared/rules.py.

Arrow semantics per code (see execute_step in rules.py):
    0  [0, i, j, -, -]  lone pair on i forms bond i-j
    1  [1, i, j, -, l]  lone pair on i attacks j, bond j-l breaks onto l
    2  [2, i, j, k, -]  bond i-k forms bond i-j
    3  [3, i, j, k, l]  bond i-k forms bond i-j, bond j-l breaks onto l
    4  [4, i, j, -, -]  lone pair on i takes H from j, bond j-H breaks onto j
    5  [5, i, j, k, -]  bond i-k takes H from j, bond j-H breaks onto j
    6  [6, -, j, i, -]  hydride from i (bond i-H) to j
    7  [7, -, j, i, l]  hydride from i (bond i-H) to j, bond j-l breaks onto l
    8  [8, i, j, k, l]  i takes H from j, bond j-H becomes pi bond j-k, bond k-l breaks onto l
    9  [9, i, j, k, -]  i takes H from j, bond j-H becomes pi bond j-k (k is a cation)
    10 [10, -, j, -, l] bond j-l breaks onto l

Usage:
    from shared.curly_arrows import draw_mechanism
    draw_mechanism(mol, [1, 2, 0, None, 1])          # IPython SVG
    draw_mechanism(mol, mech, fmt='png', path='a.png')
"""

import warnings

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Geometry import Point2D

ARROW_COLOUR = (0.85, 0.1, 0.1)

# Endpoint descriptors (all indices refer to the render mol):
#   ('lp', a)        lone pair on atom a
#   ('bond', a, b)   middle of bond a-b
#   ('atom', a)      electrons end up on atom a
#   ('form', a, b)   new bond forming between a and b (a is the nucleophile side)


def normalise_mechanism(mechanism):
    """Convert legacy layouts (as found in training/) to the current one:
    [1, i, j, k, None] was bond->atom (now code 2), and codes 6/7 used to
    store the hydride donor in slot 1 rather than slot 3."""
    code, i, j, k, l = (list(mechanism) + [None] * 5)[:5]
    if code == 1 and l is None and k is not None:
        code = 2
    if code in (6, 7) and i is not None and k is None:
        i, k = None, i
    return [code, i, j, k, l]


def mechanism_to_arrows(mechanism, h_on=None):
    """Return a list of (start, end) endpoint descriptors for a mechanism.
    `h_on` maps a heavy atom index to the explicit H index drawn on it."""
    code, i, j, k, l = normalise_mechanism(mechanism)
    h_on = h_on or {}
    if code == 0:
        return [(('lp', i), ('form', i, j))]
    if code == 1:
        return [(('lp', i), ('form', i, j)), (('bond', j, l), ('atom', l))]
    if code == 2:
        return [(('bond', i, k), ('form', i, j))]
    if code == 3:
        return [(('bond', i, k), ('form', i, j)), (('bond', j, l), ('atom', l))]
    if code == 4:
        h = h_on[j]
        return [(('lp', i), ('form', i, h)), (('bond', j, h), ('atom', j))]
    if code == 5:
        h = h_on[j]
        return [(('bond', i, k), ('form', i, h)), (('bond', j, h), ('atom', j))]
    if code == 6:
        h = h_on[k]
        return [(('bond', k, h), ('form', h, j))]
    if code == 7:
        h = h_on[k]
        return [(('bond', k, h), ('form', h, j)), (('bond', j, l), ('atom', l))]
    if code == 8:
        h = h_on[j]
        return [(('lp', i), ('form', i, h)), (('bond', j, h), ('form', j, k)),
                (('bond', k, l), ('atom', l))]
    if code == 9:
        h = h_on[j]
        return [(('lp', i), ('form', i, h)), (('bond', j, h), ('form', j, k))]
    if code == 10:
        return [(('bond', j, l), ('atom', l))]
    raise ValueError(f'Unknown mechanism code {code}')


def _atoms_needing_h(mechanism):
    """[(atom, X-H bond length)] for atoms that need an explicit H drawn."""
    code, i, j, k, l = normalise_mechanism(mechanism)
    if code in (4, 5, 8, 9):
        return [(j, 1.5)]
    if code in (6, 7):
        return [(k, 1.9)]
    return []


def lone_pairs(atom):
    """Number of non-bonding electron pairs on an atom."""
    outer = Chem.GetPeriodicTable().GetNOuterElecs(atom.GetAtomicNum())
    nonbonding = outer - atom.GetFormalCharge() - atom.GetTotalValence() - atom.GetNumRadicalElectrons()
    return max(0, nonbonding // 2)


def _add_explicit_h(mol, atom_idx, bond_length=1.5):
    """Add one explicit H to atom_idx, placed in 2D in the clearest direction
    (RDKit's 2D bond length is 1.5). Keeps all existing atom indices;
    returns (mol, h_idx)."""
    conf = mol.GetConformer()
    xy = conf.GetPositions()[:, :2]
    pos = xy[atom_idx]
    nbr_vecs = []
    for n in mol.GetAtomWithIdx(atom_idx).GetNeighbors():
        v = xy[n.GetIdx()] - pos
        if np.linalg.norm(v) > 1e-6:
            nbr_vecs.append(v / np.linalg.norm(v))
    others = np.delete(xy, atom_idx, axis=0)
    best = None
    for ang in np.radians(np.arange(0, 360, 10)):
        d = np.array([np.cos(ang), np.sin(ang)])
        # keep away from existing bonds on this atom...
        score = sum(np.exp(-((1 - d @ v) / 0.35) ** 2) * 3 for v in nbr_vecs)
        # ...and from other atoms near both the H and the middle of the new bond
        for frac in (0.5, 1.0):
            if len(others):
                dist = np.linalg.norm(others - (pos + d * bond_length * frac), axis=1)
                score += np.sum(np.exp(-(dist / 0.9) ** 2))
        if best is None or score < best[0]:
            best = (score, d)
    direction = best[1]

    rw = Chem.RWMol(mol)
    atom = rw.GetAtomWithIdx(atom_idx)
    if atom.GetNumExplicitHs() > 0:
        atom.SetNumExplicitHs(atom.GetNumExplicitHs() - 1)
    h_idx = rw.AddAtom(Chem.Atom(1))
    rw.AddBond(atom_idx, h_idx, Chem.BondType.SINGLE)
    new_pos = pos + direction * bond_length
    rw.GetConformer().SetAtomPosition(h_idx, (float(new_pos[0]), float(new_pos[1]), 0.0))
    out = rw.GetMol()
    out.UpdatePropertyCache(strict=False)
    return out, h_idx


def _bezier(p0, p1, p2, p3, n=60):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else np.array([1.0, 0.0])


class _ArrowPlanner:
    """Turns endpoint descriptors into pixel-space Bezier curves, choosing the
    side to bow towards so the arrow avoids atoms and other arrows."""

    def __init__(self, mol, pos, bond_len):
        self.mol = mol
        self.pos = pos
        self.bl = bond_len
        self.obstacles = list(pos.values())
        for b in mol.GetBonds():
            a, c = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
            self.obstacles.append((pos[a] + pos[c]) / 2)
        self.obstacles = np.array(self.obstacles)
        self.placed = []  # sampled points of arrows already planned

    def _crowding(self, pts):
        score = 0.0
        d = np.linalg.norm(pts[:, None, :] - self.obstacles[None, :, :], axis=2)
        score += np.sum(np.exp(-(d / (0.45 * self.bl)) ** 2))
        for other in self.placed:
            d = np.linalg.norm(pts[:, None, :] - other[None, :, :], axis=2)
            score += 2.0 * np.sum(np.exp(-(d / (0.35 * self.bl)) ** 2))
        return score

    def _anchor(self, desc, side_hint):
        kind = desc[0]
        if kind == 'bond':
            return (self.pos[desc[1]] + self.pos[desc[2]]) / 2
        return self.pos[desc[1]]

    def _lp_geometry(self, atom_pos, u, side):
        """Centre of the lone-pair dots and the arrow start just beyond them."""
        out = _unit(side + 0.35 * u)
        return atom_pos + out * 0.36 * self.bl, atom_pos + out * 0.5 * self.bl, out

    def plan(self, start, end):
        p_start = self._anchor(start, None)
        if end[0] == 'atom':
            p_end_raw = self.pos[end[1]]
        else:  # 'form'
            a, b = end[1], end[2]
            pa, pb = self.pos[a], self.pos[b]
            if self.mol.GetBondBetweenAtoms(int(a), int(b)) is not None:
                p_end_raw = (pa + pb) / 2          # forming a pi bond: aim at the bond
            else:
                p_end_raw = pb                      # forming a new bond: aim at the target atom
        chord = p_end_raw - p_start
        dist = np.linalg.norm(chord)
        u = _unit(chord)
        perp = np.array([-u[1], u[0]])

        best = None
        for sign in (1, -1):
            pts, ctrl = self._curve(start, end, p_start, p_end_raw, dist, u, sign * perp)
            score = self._crowding(pts[5:-5]) if len(pts) > 10 else 0
            lp = None
            if start[0] == 'lp':
                centre, _, out = self._lp_geometry(p_start, u, sign * perp)
                lp = (centre, out)
                # the dots need room too, away from the atom's own bonds
                score += 4 * self._crowding(centre[None, :])
            if best is None or score < best[0]:
                best = (score, pts, lp)
        self.placed.append(best[1])
        return best[1], best[2]

    def _curve(self, start, end, p0, p3, dist, u, side):
        bl = self.bl
        short = dist < 1.3 * bl
        if start[0] == 'bond' and end[0] == 'atom':
            # Bond breaking onto one of its own atoms: a tight hook from the
            # bond middle that lands beside the atom, pointing at it.
            p0 = p0 + side * 0.08 * bl
            p3 = p3 + side * 0.36 * bl - u * 0.02 * bl
            c1 = p0 + side * 0.5 * bl - u * 0.05 * bl
            c2 = p3 + side * 0.4 * bl + u * 0.22 * bl
            return _bezier(p0, c1, c2, p3), (p0, c1, c2, p3)
        if (start[0] == 'bond' and end[0] == 'form' and end[1] in start[1:]
                and self.mol.GetBondBetweenAtoms(int(end[1]), int(end[2])) is None):
            return self._curve_via_pivot(start, end, side)
        # Start just beyond the lone-pair dots
        if start[0] == 'lp':
            p0 = self._lp_geometry(p0, u, side)[1]
        # Stop short of the target so the head doesn't sit on the label
        if end[0] == 'atom':
            p3 = p3 + side * 0.28 * bl - u * 0.12 * bl
        elif end[0] == 'form' and self.mol.GetBondBetweenAtoms(int(end[1]), int(end[2])) is None:
            p3 = p3 - u * min(0.3 * bl, 0.3 * dist) + side * 0.12 * bl
        else:
            p3 = p3 + side * 0.18 * bl
        chord = p3 - p0
        d = np.linalg.norm(chord)
        bow = (0.55 if short else 0.32) * d
        bow = min(bow, 1.6 * bl)
        c1 = p0 + chord * 0.15 + side * bow
        c2 = p0 + chord * 0.85 + side * bow
        return _bezier(p0, c1, c2, p3), (p0, c1, c2, p3)


    def _curve_via_pivot(self, start, end, side):
        """Bond -> new bond: leave the middle of the old bond, sweep over the
        atom that keeps the electrons (the pivot), then on to the target."""
        bl = self.bl
        pivot, target = end[1], end[2]
        other = start[2] if start[1] == pivot else start[1]
        pp, po, pt = self.pos[pivot], self.pos[other], self.pos[target]
        bond_dir = _unit(pp - po)

        p0 = (pp + po) / 2 + side * 0.1 * bl
        via = pp + bond_dir * 0.06 * bl + side * 0.08 * bl
        u2 = _unit(pt - via)
        d2 = np.linalg.norm(pt - via)
        p3 = pt - u2 * min(0.3 * bl, 0.3 * d2) + side * 0.1 * bl
        t_via = _unit(bond_dir + u2)

        l1 = np.linalg.norm(via - p0)
        seg1 = _bezier(p0, p0 + _unit(bond_dir + 0.6 * side) * 0.4 * l1, via - t_via * 0.4 * l1, via, n=24)
        l2 = np.linalg.norm(p3 - via)
        bow = min(0.25 * l2, 1.2 * bl)
        c3 = via + t_via * 0.4 * l2
        c4 = p3 + side * bow - u2 * 0.25 * l2
        seg2 = _bezier(via, c3, c4, p3, n=48)
        pts = np.vstack([seg1, seg2[1:]])
        return pts, (p0, via, c4, p3)


def _stroke_polygon(pts, width):
    """Outline a polyline as a closed polygon of the given width."""
    tang = np.gradient(pts, axis=0)
    norms = np.array([_unit(np.array([-t[1], t[0]])) for t in tang])
    left = pts + norms * width / 2
    right = pts - norms * width / 2
    return np.vstack([left, right[::-1]])


def _arrowhead(tip, direction, size):
    d = _unit(direction)
    p = np.array([-d[1], d[0]])
    back = tip - d * size
    notch = tip - d * size * 0.7
    return np.array([tip, back + p * size * 0.45, notch, back - p * size * 0.45])


def _circle(centre, r, n=16):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return [Point2D(*(centre + r * np.array([np.cos(a), np.sin(a)]))) for a in t]


def _draw_lone_pair(drawer, centre, out, bl, colour=(0, 0, 0)):
    along = np.array([-out[1], out[0]])
    r = max(1.8, 0.055 * bl)
    drawer.SetColour(colour)
    drawer.SetFillPolys(True)
    drawer.SetLineWidth(0)
    for s in (-1, 1):
        drawer.DrawPolygon(_circle(centre + along * s * 0.09 * bl, r), rawCoords=True)


def _draw_arrow(drawer, pts, width, head_size, colour):
    # trim the curve so the shaft ends inside the head rather than poking out
    tip = pts[-1]
    direction = pts[-1] - pts[-4]
    cum = np.cumsum(np.r_[0, np.linalg.norm(np.diff(pts, axis=0), axis=1)])
    keep = cum <= cum[-1] - head_size * 0.6
    shaft = pts[keep] if keep.sum() >= 2 else pts[:2]

    drawer.SetColour(colour)
    drawer.SetFillPolys(True)
    drawer.SetLineWidth(0)
    drawer.DrawPolygon([Point2D(*p) for p in _stroke_polygon(shaft, width)], rawCoords=True)
    drawer.DrawPolygon([Point2D(*p) for p in _arrowhead(tip, direction, head_size)], rawCoords=True)


def render_mechanism(mol, mechanism, size=None, fmt='svg', colour=ARROW_COLOUR,
                     atom_indices=False, highlight=True, legend='', lone_pair_dots=True):
    """Render `mol` with the curly arrows for one mechanism vector.
    Returns SVG text (fmt='svg') or PNG bytes (fmt='png')."""
    mechanism = normalise_mechanism(mechanism)
    mol = Chem.Mol(mol)
    for a in mol.GetAtoms():
        a.SetAtomMapNum(0)
    mol.UpdatePropertyCache(strict=False)
    if mol.GetNumConformers() == 0:
        rdDepictor.Compute2DCoords(mol)
    if size is None:
        xy = mol.GetConformer().GetPositions()[:, :2]
        span = xy.max(axis=0) - xy.min(axis=0)
        # ~45 px per bond (RDKit 2D bond length is 1.5)
        size = tuple(int(np.clip(s * 30 + 160, 300, 1400)) for s in span)

    h_on = {}
    for a, h_len in _atoms_needing_h(mechanism):
        if a is not None and a not in h_on:
            mol, h_on[a] = _add_explicit_h(mol, a, bond_length=h_len)
    arrows = mechanism_to_arrows(mechanism, h_on)
    for start, _ in arrows:
        if start[0] == 'bond' and mol.GetBondBetweenAtoms(int(start[1]), int(start[2])) is None:
            warnings.warn(f'Mechanism {mechanism}: atoms {start[1]} and {start[2]} are not bonded '
                          'in this mol - the indices probably refer to a different atom ordering')

    w, h = size
    drawer = rdMolDraw2D.MolDraw2DSVG(w, h) if fmt == 'svg' else rdMolDraw2D.MolDraw2DCairo(w, h)
    opts = drawer.drawOptions()
    opts.padding = 0.15
    opts.addAtomIndices = atom_indices
    opts.clearBackground = True

    involved = sorted({x for x in mechanism[1:] if x is not None} | set(h_on.values()))
    hl_atoms = involved if highlight else []
    hl_colours = {a: (1.0, 0.85, 0.6) for a in hl_atoms}
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend=legend, highlightAtoms=hl_atoms,
                                       highlightAtomColors=hl_colours, highlightBonds=[],
                                       kekulize=True)

    pos = {a.GetIdx(): np.array([drawer.GetDrawCoords(a.GetIdx()).x, drawer.GetDrawCoords(a.GetIdx()).y])
           for a in mol.GetAtoms()}
    bond_lens = [np.linalg.norm(pos[b.GetBeginAtomIdx()] - pos[b.GetEndAtomIdx()]) for b in mol.GetBonds()]
    bl = float(np.median(bond_lens)) if bond_lens else 0.15 * min(w, h)

    planner = _ArrowPlanner(mol, pos, bl)
    width = max(1.5, 0.045 * bl)
    head = max(7.0, 0.22 * bl)
    for start, end in arrows:
        pts, lp = planner.plan(start, end)
        if lone_pair_dots and lp is not None and lone_pairs(mol.GetAtomWithIdx(start[1])) > 0:
            _draw_lone_pair(drawer, lp[0], lp[1], bl)
        _draw_arrow(drawer, pts, width, head, colour)

    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def draw_mechanism(mol, mechanism, size=None, fmt='svg', path=None, **kwargs):
    """Notebook-friendly wrapper: returns an IPython SVG/Image object, and
    writes to `path` if given."""
    out = render_mechanism(mol, mechanism, size=size, fmt=fmt, **kwargs)
    if path is not None:
        mode = 'w' if fmt == 'svg' else 'wb'
        with open(path, mode) as f:
            f.write(out)
    from IPython.display import SVG, Image
    return SVG(out) if fmt == 'svg' else Image(out)


def draw_case(case_dir, only_probable=None, fmt='svg', **kwargs):
    """Display every mechanism in a training/finetuning case folder
    (sm.pkl + data.json). `only_probable` filters on the 'probable' label."""
    import json
    import pickle
    from pathlib import Path
    from IPython.display import display
    case_dir = Path(case_dir)
    mol = pickle.loads((case_dir / 'sm.pkl').read_bytes())
    choices = json.loads((case_dir / 'data.json').read_text())['choices']
    for key in sorted(choices, key=int):
        choice = choices[key]
        if only_probable is not None and choice.get('probable') != only_probable:
            continue
        legend = f"{key}: {choice['mechanism']}  probable={choice.get('probable')}"
        display(draw_mechanism(mol, choice['mechanism'], fmt=fmt, legend=legend, **kwargs))
