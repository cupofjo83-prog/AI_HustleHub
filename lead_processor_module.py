import tkinter as tk
from tkinter import ttk, scrolledtext
import csv

# --- 1. The Fixed Email Template (Your Closing/Pitch Structure) ---
EMAIL_TEMPLATE = """
Hello,

My name is Joe, and I'm a local business owner from the Iron Range. I'm reaching out because I specialize in **automated bulk content creation**—a perfect match for businesses like yours.

I use a custom Linux/AI script to take your raw product data and instantly generate **unique, SEO-optimized listings in just 48 hours.**

**Here is the content quality we deliver for your premium line:**
*[AI_PITCH_SAMPLE_PLACEHOLDER]*

This service ensures every item in your store is searchable and ready for the next seasonal rush, dramatically cutting your annual content costs.

I'd appreciate the chance to discuss how a fellow local can help automate this critical bottleneck. I'm available for a quick call or a local handshake if you prefer.

Thank you for your time,
RuralJoe
"""

# --- 2. Data Storage ---
LEAD_DATA = []

# --- 3. Core Functions ---

def load_leads_from_csv(file_path='leads.csv'):
    """Reads the CSV file and populates the global LEAD_DATA list."""
    global LEAD_DATA
    LEAD_DATA = []  # Clear previous data

    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            # Assumes CSV columns: Business_Name, Contact_Email, Product_Focus, AI_Pitch_Sample
            reader = csv.DictReader(file)
            for row in reader:
                LEAD_DATA.append(row)

        # Populate the Listbox with business names
        listbox_leads.delete(0, tk.END)
        for i, lead in enumerate(LEAD_DATA):
            listbox_leads.insert(tk.END, f"{i+1}. {lead.get('Business_Name', 'N/A')}")

        update_status(f"Successfully loaded {len(LEAD_DATA)} leads.")

    except FileNotFoundError:
        update_status("ERROR: 'leads.csv' not found. Please create the file.")
    except Exception as e:
        update_status(f"ERROR loading CSV: {e}")

def generate_email_on_click(event):
    """Generates the full email when a lead is clicked in the listbox."""
    try:
        # Get the index of the selected item
        selected_index = listbox_leads.curselection()[0]
        lead = LEAD_DATA[selected_index]

        # 1. Assemble the Subject Line
        subject_line = f"Local AI: Automating Descriptions for Your {lead['Product_Focus']}"

        # 2. Assemble the Email Body (using the placeholder)
        email_body = EMAIL_TEMPLATE.replace('*[AI_PITCH_SAMPLE_PLACEHOLDER]*', lead['AI_Pitch_Sample'])

        # 3. Format the final output for the text box
        final_output = (
            f"**LEAD: {lead['Business_Name'].upper()} **\n"
            f"{'-'*50}\n"
            f"**TO:** {lead['Contact_Email']}\n"
            f"**SUBJECT:** {subject_line}\n"
            f"{'-'*50}\n"
            f"*** COPY EMAIL BODY BELOW ***\n\n"
            f"{email_body}"
        )

        # Insert into the read-only output box
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, final_output)
        update_status(f"Email generated for: {lead['Business_Name']}")

    except IndexError:
        update_status("Please select a lead to generate the email.")
    except Exception as e:
        update_status(f"Generation ERROR: {e}")

def update_status(message):
    """Updates the status bar at the bottom of the GUI."""
    label_status.config(text=f"Status: {message}")


# --- 4. GUI Setup (Assuming this is added to your main Tkinter window) ---

# We'll assume 'root' is your main Tkinter window instance
root = tk.Tk()
root.title("Joe's AI Hustle Hub - Email List Processor")

# Create a container frame
frame_main = ttk.Frame(root, padding="10")
frame_main.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# --- Left Side: Lead List ---
label_list = ttk.Label(frame_main, text="Leads (Click to Generate Email):")
label_list.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

listbox_leads = tk.Listbox(frame_main, height=20, width=50)
listbox_leads.grid(row=1, column=0, rowspan=3, sticky=(tk.W, tk.E))
listbox_leads.bind('<<ListboxSelect>>', generate_email_on_click) # Bind the click event

scrollbar_leads = ttk.Scrollbar(frame_main, orient=tk.VERTICAL, command=listbox_leads.yview)
scrollbar_leads.grid(row=1, column=1, rowspan=3, sticky=(tk.N, tk.S))
listbox_leads['yscrollcommand'] = scrollbar_leads.set

# Button to load the data
btn_load = ttk.Button(frame_main, text="Load Leads.csv", command=load_leads_from_csv)
btn_load.grid(row=4, column=0, pady=(10, 0), sticky=tk.W)


# --- Right Side: Output Area ---
label_output = ttk.Label(frame_main, text="Generated Email (Copy & Paste):")
label_output.grid(row=0, column=2, sticky=tk.W, pady=(0, 5), padx=(10, 0))

text_output = scrolledtext.ScrolledText(frame_main, wrap=tk.WORD, height=25, width=70)
text_output.grid(row=1, column=2, rowspan=4, sticky=(tk.W, tk.E), padx=(10, 0))


# --- Status Bar ---
label_status = ttk.Label(root, text="Status: Ready. Load 'leads.csv'.", relief=tk.SUNKEN, anchor=tk.W)
label_status.grid(row=1, column=0, sticky=(tk.W, tk.E))


# Run the application
# If you are integrating this into a larger hub, you would remove root.mainloop()
# and instead call the setup functions within your main hub class.
# root.mainloop()
