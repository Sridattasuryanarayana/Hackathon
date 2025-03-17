import os
import streamlit as st
import google.generativeai as genai
from datetime import datetime
import pandas as pd
from fpdf import FPDF  # For PDF generation

class OnboardMateAgent:
    def __init__(self, api_key, model_name="gemini-2.0-flash-exp"):
        # Configure API
        genai.configure(api_key=api_key)

        # Generation configuration
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        # Create the model with system instruction
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.generation_config,
        )

    def generate_onboarding_plan(self, employee_data):
        """
        Generate a personalized onboarding plan for a new hire.
        """
        prompt_template = """Create a personalized onboarding plan for a new hire with the following details:

        *   **Name:** {name}
        *   **Role:** {role}
        *   **Department:** {department}
        *   **Start Date:** {start_date}
        *   **Previous Experience:** {previous_experience}
        *   **Onboarding Goals:** {goals}

        The plan should include:
        - A checklist of tasks to be completed
        - A schedule of onboarding sessions
        - Links to relevant training materials
        - Key contacts and resources

        Write the onboarding plan in a clear and concise format.
        """

        final_prompt = prompt_template.format(**employee_data)

        chat = self.model.start_chat(history=[])  # Start new session
        try:
            response = chat.send_message(final_prompt)
            if response.candidates and response.candidates[0].finish_reason == "RECITATION":
                print("RECITATION STOPPED")
                return None  # Indicate failure, you may want to retry here.
            else:
                return response.text
        except genai.types.generation_types.StopCandidateException as e:
            print(f"Error: {e}")
            return None  # Indicate failure

    def provide_knowledge_assistance(self, query):
        """
        Provide real-time knowledge assistance to new hires.
        """
        response = self.model.start_chat(history=[]).send_message(
            f"Provide a detailed response to the following query from a new hire:\n\n{query}"
        )
        return response.text

def render_download_button(content, file_name, mime_type="text/plain"):
    """
    Render a download button for content.
    """
    st.download_button(
        label="📥 Download",
        data=content,
        file_name=file_name,
        mime=mime_type,
    )

def save_to_excel(data, file_path="onboarding_data.xlsx"):
    """
    Save employee data to an Excel file.
    """
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        new_df = pd.DataFrame([data])
        df = pd.concat([df, new_df], ignore_index=True)
    else:
        df = pd.DataFrame([data])
    
    df.to_excel(file_path, index=False)

def generate_pdf(content, file_name="onboarding_plan.pdf"):
    """
    Generate a PDF file from the onboarding plan content.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add content to the PDF
    for line in content.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)

    # Save the PDF
    pdf.output(file_name)
    return file_name

def main():
    # Set page configuration
    st.set_page_config(
        page_title="OnboardMate - AI-Powered Employee Onboarding",
        page_icon="👤",
        layout="wide",
    )

    # Title
    st.title("👤 OnboardMate - AI-Powered Employee Onboarding")
    st.markdown("Streamline and personalize the employee onboarding process with the help of AI.")

    # Fetch API Key from environment variables
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        st.error("API key not found in environment variables! Set GEMINI_API_KEY.")
        return

    # Initialize OnboardMate Agent
    onboard_mate_agent = OnboardMateAgent(api_key)

    # Tabs for Onboarding Plan and Knowledge Assistance
    tab1, tab2 = st.tabs(["📋 Onboarding Plan", "📚 Knowledge Assistance"])

    with tab1:
        st.subheader("📋 Onboarding Plan")
        st.markdown("Please provide the following details for the new hire:")

        # Input fields for the new hire's details
        name = st.text_input("Name", placeholder="e.g. AKELLA SRI DATTA SURYANARAYANA", key="onboard_name")
        role = st.text_input("Role", placeholder="e.g. Software Engineer", key="onboard_role")
        department = st.text_input("Department", placeholder="e.g. Engineering", key="onboard_department")
        start_date = st.date_input("Start Date", key="onboard_start_date")
        previous_experience = st.text_area("Previous Experience", placeholder="e.g. 5 years of experience in software development", key="onboard_experience")
        goals = st.text_area("Onboarding Goals", placeholder="e.g. Get familiar with the codebase, understand the team's workflow", key="onboard_goals")

        if st.button("Generate Onboarding Plan", key="btn_generate_plan"):
            if any([name.strip(), role.strip(), department.strip(), start_date, previous_experience.strip(), goals.strip()]):
                employee_data = {
                    "name": name,
                    "role": role,
                    "department": department,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "previous_experience": previous_experience,
                    "goals": goals,
                }
                with st.spinner("Generating onboarding plan..."):
                    onboarding_plan = onboard_mate_agent.generate_onboarding_plan(employee_data)
                if onboarding_plan:
                    st.markdown("### Generated Onboarding Plan")
                    st.markdown(onboarding_plan, unsafe_allow_html=True)

                    # Save employee data to Excel
                    save_to_excel(employee_data)
                    st.success("Employee details saved to Excel file.")

                    # Generate and download PDF
                    pdf_file = generate_pdf(onboarding_plan)
                    with open(pdf_file, "rb") as file:
                        st.download_button(
                            label="📥 Download PDF",
                            data=file,
                            file_name="onboarding_plan.pdf",
                            mime="application/pdf",
                        )
                else:
                    st.error("Onboarding plan generation failed due to recitation issues or an error. Please adjust the inputs.")
            else:
                st.warning("Please provide required details for the onboarding plan (Name, Role, Department, Start Date, Previous Experience, and Goals).")

        # Display saved employee data
        if os.path.exists("onboarding_data.xlsx"):
            st.subheader("📊 Saved Employee Data")
            df = pd.read_excel("onboarding_data.xlsx")
            st.dataframe(df)

    with tab2:
        st.subheader("📚 Knowledge Assistance")
        st.markdown("Ask any question related to your onboarding process or role.")

        # Example questions
        st.markdown("### Example Questions")
        example_questions = [
            "Where can I find the project documentation?",
            "What is the process for requesting time off?",
            "How do I set up my email account?",
            "Where can I find the employee handbook?",
            "What are the core working hours?",
            "How do I access the company's intranet?",
        ]
        for question in example_questions:
            st.markdown(f"- {question}")

        # Input field for knowledge query
        query = st.text_area("Enter your query", placeholder="e.g. Where can I find the project documentation?", key="knowledge_query")

        if st.button("Get Assistance", key="btn_get_assistance"):
            if query.strip():
                with st.spinner("Fetching knowledge assistance..."):
                    knowledge_response = onboard_mate_agent.provide_knowledge_assistance(query)
                st.markdown("### Knowledge Assistance")
                st.markdown(knowledge_response, unsafe_allow_html=True)
            else:
                st.warning("Please enter a query to get assistance.")

        # General FAQs
        st.markdown("### General FAQs")
        faqs = {
            "How do I set up my email account?": "You can set up your email account by following the instructions provided in the onboarding email. If you need further assistance, contact IT support.",
            "What is the process for requesting time off?": "You can request time off by submitting a request through the HR portal. Make sure to get approval from your manager.",
            "Where can I find the employee handbook?": "The employee handbook is available on the company's intranet under the 'Resources' section.",
            "What are the core working hours?": "The core working hours are from 9 AM to 5 PM, Monday to Friday.",
            "How do I access the company's intranet?": "You can access the intranet by logging in with your company credentials at intranet.company.com.",
            "What is the dress code policy?": "The company follows a business casual dress code. Please refer to the employee handbook for more details.",
            "How do I request IT support?": "You can request IT support by submitting a ticket through the IT support portal or by calling the IT helpdesk.",
            "What are the key contacts in my department?": "You can find the key contacts in your department by checking the department directory on the intranet.",
            "How do I enroll in benefits?": "You can enroll in benefits by logging into the HR portal and following the enrollment instructions.",
            "What is the process for submitting expenses?": "You can submit expenses by filling out the expense report form available on the HR portal and submitting it for approval.",
            "How do I access training materials?": "Training materials are available on the company's learning management system (LMS). You can access it through the intranet.",
            "What is the company's policy on remote work?": "The company allows remote work for certain roles. Please check with your manager and refer to the remote work policy in the employee handbook.",
            "How do I schedule a meeting room?": "You can schedule a meeting room by using the room booking system available on the intranet.",
            "What are the company's core values?": "The company's core values are integrity, innovation, collaboration, and excellence.",
            "How do I report a technical issue?": "You can report a technical issue by submitting a ticket through the IT support portal or by contacting the IT helpdesk.",
            "What is the process for performance reviews?": "Performance reviews are conducted bi-annually. You will receive a notification from HR with instructions on how to prepare.",
            "How do I update my personal information in the system?": "You can update your personal information by logging into the HR portal and navigating to the 'My Profile' section.",
            "What are the company's social media guidelines?": "The company's social media guidelines are available in the employee handbook. Please review them before posting on social media.",
            "How do I request business cards?": "You can request business cards by submitting a request through the HR portal. Make sure to include your design preferences.",
        }
        for question, answer in faqs.items():
            with st.expander(question):
                st.markdown(answer)

if __name__ == "__main__":
    main()