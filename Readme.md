python -m venv venv
venv\Scripts\activate  # On Windows

to run the file 
streamlit run filter_tool.py


test1 =>  done


✅ Supports both CSV and Excel (.xlsx) file upload
✅ Lets user select sheet (if Excel)
✅ Allows filter column selection and manual value entry
✅ Lets you choose output columns to display
✅ Shows filtered results and raw preview



test 2 => done


Upload two Excel files.

Manually select sheet and column from each.

Filter Sheet2 where a selected column contains any value from a selected column in Sheet1.

On the filtered result, apply additional filter on another column:

Contains filter with multiple manual inputs.

Exact match with multiple values.

Select output columns from Sheet2 manually.

 
test3 => done 


Upload two Excel files

Select comparison columns

Perform exact or case-insensitive match

Select output columns manually from both File 1 and File 2

Download the final matched result as CSV



test4 => 

📁 Upload two Excel files

📄 Manually select sheets and columns from both files

🔍 Use contains (Excel-style partial matching) between selected columns

✅ Output should show only matched rows

🧾 Let the user select any columns from both files to include in output


Main test =>

🛠️ To Run:
Save this as main.py, then run:

bash
Copy
Edit

streamlit run main.py

Let me know if you want to:

Add fuzzy matching

Support CSV for comparator tools

Save/load settings

Or turn this into a standalone app with authentication and history