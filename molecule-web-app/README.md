# Molecule Web App

This project is a web application that allows users to draw chemical structures using Marvin JS, convert them to SMILES strings, and process these strings using predefined rules for chemical reactions. The application is structured into a backend and a frontend, with the backend handling the logic and the frontend providing the user interface.

## Project Structure

```
molecule-web-app
├── backend
│   ├── app.py                # Main entry point for the backend application
│   ├── rules
│   │   └── rules.ipynb      # Jupyter Notebook with rules for processing molecules
│   └── requirements.txt      # Python dependencies for the backend
├── frontend
│   ├── index.html            # Main HTML file for the frontend application
│   ├── styles
│   │   └── style.css         # CSS styles for the frontend application
│   ├── scripts
│   │   └── app.js            # JavaScript code for handling user interactions
│   └── assets                # Directory for additional assets (images, icons, etc.)
└── README.md                 # Documentation for the project
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd molecule-web-app
   ```

2. **Set up the backend:**
   - Navigate to the `backend` directory.
   - Create a virtual environment (optional but recommended):
     ```
     python -m venv venv
     source venv/bin/activate  # On Windows use `venv\Scripts\activate`
     ```
   - Install the required dependencies:
     ```
     pip install -r requirements.txt
     ```

3. **Run the backend server:**
   ```
   python app.py
   ```

4. **Set up the frontend:**
   - Open `index.html` in a web browser to access the application.

## Usage Guidelines

- Use the Marvin JS interface to draw a molecule.
- Once the molecule is drawn, the application will convert it to a SMILES string and process it using the rules defined in `rules.ipynb`.
- The resulting molecules will be displayed as clickable images, allowing you to rerun the program using their SMILES as input.

## Additional Information

- Ensure that you have the necessary permissions and licenses to use Marvin JS in your project.
- For any issues or contributions, please refer to the project's GitHub page.

## License

This project is licensed under the MIT License - see the LICENSE file for details.