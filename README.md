
# Project Monitoring Form Document Generator

An automated Word document generator for Software Engineering Project Monitoring forms (SPMP, SRS, SDD). This project uses a hybrid approach: **Jinja2 templating** (`docxtpl`) for perfect layout formatting of metadata and signatures, and **native Python Word processing** (`python-docx`) to cleanly inject matrix table rows without breaking invisible XML tags.

## Prerequisites
- Python 3.13 or 3.14 installed on your system.


---

## Quick Start (The Simplest Way)

You can set this up using standard Python tools right in your terminal or command prompt.

**1. Create a virtual environment (Recommended)**
This keeps the project's dependencies separate from your main system.

```bash
python -m venv .venv

```

**2. Activate the virtual environment**

* **Windows:**
```bash
.venv\Scripts\activate

```


* **Mac / Linux:**
```bash
source .venv/bin/activate

```



**3. Install the required libraries**

```bash
pip install -r requirements.txt

```

**4. Generate the document**

```bash
python generate_doc.py

```

*Look inside the newly created `outputs/` folder for your finished `SPMP_Monitoring_Final.docx` file!*

---

## Optional: Conda Setup (Isolated Directory Approach)

If you prefer using Conda but want to keep the environment strictly inside the project folder (similar to the standard `.venv` approach), use these steps:

**1. Create the local Conda environment**
This builds the environment in a hidden `.venv` folder right inside your project directory.
```bash
conda create --prefix ./.venv python=3.13 -y

```

**2. Activate the local environment (or place it in a .sh file)**

```bash
conda activate ./.venv

```

**3. Install the required libraries**

```bash
pip install -r requirements.txt

```

**4. Generate the document**

```bash
python generate_doc.py

```


---

## How to Customize

* **To change the form data:** Edit `input_data.json`. This controls the project title, candidate names, and the specific corrections/checkmarks in the table.
* **To change the visual layout:** Open `template.docx` in Microsoft Word. You can adjust margins, fonts, table border colors, and spacing. Save it, and the Python script will instantly inherit your new visual design.
* **To handle large tables:** For bulk-editing the monitoring matrix rows, consider using the included `manage_monitoring_csv.py` tool to edit your rows in Excel/CSV format and import them back into the JSON file.
