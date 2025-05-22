import autogen
import streamlit as st
import os
from docx import Document
import docx2pdf

llm_config ={
    "model": "gpt-4o-mini",
    #for this program, you need to get an OpenAI api_key
    #You can get yours at "https://openai.com/api/pricing/", create an account, and navigate to API Login
    "api_key": ""
}

job_Name = st.text_input("Input job title here")
company_Name = st.text_input("Input company name here")
requirements=st.text_area("Input job requirements here")
cover_Letter=st.text_area("Cover Letter here")

file1, file2, file3=st.file_uploader("Upload example here", type="pdf",accept_multiple_files=True)


start_Button=st.button("Begin Writing")

writer_prompt=[
    f"""
    Using this cover letter: {cover_Letter} as well as the name of the company {company_Name},
    position that the user is applying for {job_Name} and the job requirements {requirements},
    modify the cover letter to highlight the 
    skills in the cover letter and align them job requirement. 
    Mainly rely on the information provided.
    Make sure the cover letter is grammatically sound.
    Write in full paragraphs, not bullet points.
    Use professional tone of voice throughout writing, but don't add additonal fluff or colourful language if it's not necessary.
    Include captivating hook at the start and well rounded conclusion at the end.
"""
]

writer=autogen.AssistantAgent(
    name="Writer",
    llm_config=llm_config,
    system_message=f"""
    You are a professinal writer, known for your engaging, detailed, and
    captivating cover letters. You take base cover letters and transform them 
    into compmelling documents.
    Include all information provided to you as context for your writing.
    Analyze the writing style in {file1}, {file2}, and {file3} and imitate 
    it in your writting.
"""
)

critic=autogen.AssistantAgent(
    name="Critic",
    system_message="You are a critic. You review the work of "
                "the writer and provide constructive "
                "feedback to help improve the quality of the content.",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
)

SEO_Reviewer=autogen.AssistantAgent(
    name="SEO_Reviewer",
    llm_config=llm_config,
    system_message="You are a SEO reviewer, known for" \
    "your ability to optimize content for AI software searches" \
    "ensuring that it ranks well and gets noticed by the searches"
    "Make sure your suggestion is concise (within 3 bullet points), "
    "concrete and to the point. "
    "Begin the review by stating your role.",
)

consistancy_Reviewer=autogen.AssistantAgent(
    name="Consistancy_Reviewer",
    llm_config=llm_config,
    system_message="You are a consistency reviewer, known for "
        "your ability to ensure that the written content is consistent throughout the letter " \
        "with the orignal cover letter uploaded."
        "Refer base cover letter to ensure information is correct " 
        "in case of contradictions. "
        "Make sure your suggestion is concise (within 3 bullet points), "
        "concrete and to the point. "
        "Begin the review by stating your role.",
)

completion_Reviewer=autogen.AssistantAgent(
    name="Completion_Reviewer",
    llm_config=llm_config,
    system_message="You are a content completion reviewer, known for" \
    "your ability to check that cover letters contain all required elements." \
    "You always verify that the document contains: a intro with the name of the user and job postion," \
    "body paragraphes that each highlight one soft skill and one techincal skill," \
    "and a conclusion that wraps all presented information cleanly and concisely. " \
    "Make sure your suggestion is concise (within 3 bullet points), "
    "concrete and to the point. "
    "Begin the review by stating your role.",
)

authenticity_Reviewer=autogen.AssistantAgent(
    name="Authenticity_Reviewer",
    llm_config=llm_config,
    system_message=f"""
    You are an authenticity reviewer, known for 
    your ability to perserve the unique voice of ther author. Your job
    is to ensure that the writer stays true to the oringal voice of the author even after
    making edits to the cover letter.
    Use {file1}, {file2}, {file3}, as your benchmarks to assess authenticity of writing.
    if any of these words appear:'realm, intricate, showcasing, and pivotal' prompt the writer to use another word. 
    Make sure your suggestion is concise (within 3 bullet points), 
    concrete and to the point. 
    Begin the review by stating your role.
    """,
)

meta_Reviewer=autogen.AssistantAgent(
    name="Meta_Reviewer",
    llm_config=llm_config,
    system_message="You are a meta reviewer, you aggregate and review "
    "the work of other reviewers and give a final suggestion on the content." \
    "Don't add anything additional besides your aggregated review.",
)

def  reflection_message(recipient, messages, sender, config):
    return f'''Review the following content.
            \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}'''

review_chat=[
    {"recipient": SEO_Reviewer, "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {"summary_prompt":
            "Return review into a JSON object only:"
            "{'Reviewer': '', 'Review': ''}.",},
        "max_turns": 1,},
    {"recipient": consistancy_Reviewer, "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {"summary_prompt":
            "Return review into a JSON object only:"
            "{'Reviewer': '', 'Review': ''}.",},
        "max_turns": 1,},
    {"recipient": completion_Reviewer, "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {"summary_prompt":
            "Return review into a JSON object only:"
            "{'Reviewer': '', 'Review': ''}.",},
        "max_turns": 1,},
    {"recipient": authenticity_Reviewer, "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {"summary_prompt":
            "Return review into a JSON object only:"
            "{'Reviewer': '', 'Review': ''}.",},
        "max_turns": 1,},
    {"recipient":meta_Reviewer,
        "message": "Aggregrate feedback from all reviewers and give final suggestions on the writing.",
         "max_turns": 1,},
]


critic.register_nested_chats(
    review_chat,
    trigger=writer,
)

if start_Button is True:
    with st.spinner("Agents working on the document...."):
        chat_results = autogen.initiate_chats(
            [
                {
                    "sender": critic,
                    "recipient": writer,
                    "message": writer_prompt[0],
                    "max_turns": 2,
                    "summary_method": "last_msg",
                },
            ]
        )
        st.write(chat_results[-1].chat_history[-1]["content"]) 

data = st.text_area("Paste Here")
if data:
    os.system('cp Cover_Letter_Blank.docx Cover_Letter_AI.docx')
    doc = Document('Cover_Letter_AI.docx')
    doc.add_paragraph(data)
    doc.save('Cover_Letter_AI.docx')
    os.system('docx2pdf Cover_Letter_AI.docx')
    os.system('mv Cover_Letter_AI.pdf "Your_directory_Here"')
    os.system('rm Cover_Letter_AI.docx')

