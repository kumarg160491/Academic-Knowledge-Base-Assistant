import os
import streamlit as st
from ingest import ingest_kt_session
from rag_chain import build_rag_chain, query_rag, get_all_sessions
from config import cfg

st.set_page_config(
    page_title="Lecture & Academic Knowledge Base Assistant",
    page_icon="",
    layout="wide"
)

st.title("Lecture & Academic Knowledge Base Assistant")
st.caption(
    f"LLM: {cfg.ollama.model} | "
    f"Embeddings: {cfg.ollama.embedding} | "
    f"VectorDB: ChromaDB | "
    f"Framework: LangChain"
)
st.divider()

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

"""
Sidebar: Upload and Ingest
"""
with st.sidebar:
    st.header("Upload KT Session")

    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None

    session_name  = st.text_input(
        "Session Name",
        placeholder="e.g. kafka-pipeline-onboarding",
        key=f"session_name_{st.session_state.uploader_key}"
    )
    video_file    = st.file_uploader(
        "Upload Teams Video (MP4)", 
        type=["mp4", "mkv", "avi"],
        key=f"video_file_{st.session_state.uploader_key}"
    )
    caption_file  = st.file_uploader(
        "Upload Caption File (optional)", 
        type=["vtt", "srt"],
        key=f"caption_file_{st.session_state.uploader_key}"
    )
    ref_docs      = st.file_uploader(
        "Upload Reference Documents",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "csv", "xlsx", "pptx", "py", "sql", "md", "json"],
        key=f"ref_docs_{st.session_state.uploader_key}"
    )

    ingest_btn = st.button("Ingest KT Session", type="primary", use_container_width=True)

    if ingest_btn:
        if not session_name:
            st.error("Please enter a session name.")
        elif not video_file and not ref_docs:
            st.error("Please upload either a video file or reference documents.")
        else:
            # save uploaded files to disk
            os.makedirs(cfg.data.videos_dir, exist_ok=True)
            os.makedirs(cfg.data.captions_dir, exist_ok=True)
            os.makedirs(
                os.path.join(cfg.data.documents_dir, session_name),
                exist_ok=True
            )

            video_path = None
            if video_file:
                video_path = os.path.join(cfg.data.videos_dir, video_file.name)
                with open(video_path, "wb") as f:
                    f.write(video_file.read())

            caption_path = None
            if caption_file:
                caption_path = os.path.join(cfg.data.captions_dir, caption_file.name)
                with open(caption_path, "wb") as f:
                    f.write(caption_file.read())

            for doc in ref_docs:
                doc_path = os.path.join(cfg.data.documents_dir, session_name, doc.name)
                with open(doc_path, "wb") as f:
                    f.write(doc.read())

            with st.spinner(f"Ingesting session: {session_name}..."):
                try:
                    ingest_kt_session(
                        session_name = session_name,
                        video_path   = video_path,
                        caption_path = caption_path,
                    )
                    st.cache_resource.clear()
                    st.session_state.success_msg = "Ingestion completed. Proceed with asking the question."
                    st.session_state.uploader_key += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")

    st.divider()
    st.header("Safety & Guardrails")
    enable_guardrails = st.toggle("Enable Guardrails", value=True, help="Enable input topic validation and output faithfulness check.")

    st.divider()
    st.header("System Info")
    st.code(f"""
LLM        : {cfg.ollama.model}
Embeddings : {cfg.ollama.embedding}
Whisper    : {cfg.whisper.model_size}
Top-K Docs : {cfg.retriever.top_k}
Chunk Size : {cfg.data.chunk_size}
    """)

"""
Main Area: Query
"""
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Ask a Question")

    # session selector
    try:
        sessions      = ["All Sessions"] + get_all_sessions()
        session_filter= st.selectbox("Filter by KT Session", sessions)
    except Exception:
        session_filter= "All Sessions"
        st.info("No sessions ingested yet. Upload a KT session from the sidebar.")

    # demo queries
    st.markdown("**Sample Questions:**")
    q1 = st.button("How does the Kafka pipeline work?")
    q2 = st.button("What are the steps to deploy the service?")
    # q3 = st.button("What databases are used in this project?")
    # q4 = st.button("Who is responsible for the onboarding process?")

    default_q = ""
    if q1: default_q = "How does the Kafka pipeline work?"
    elif q2: default_q = "What are the steps to deploy the service?"
    # elif q3: default_q = "What databases are used in this project?"
    # elif q4: default_q = "Who is responsible for the onboarding process?"

    question = st.text_area(
        "Your question:",
        value  = default_q,
        height = 120,
        placeholder="Ask questions from the KT sessions..."
    )

    ask_btn = st.button("Ask", type="primary", use_container_width=True)

with col2:
    st.subheader("Answer")

    if ask_btn and question.strip():

        @st.cache_resource
        def load_chain(session_filter):
            return build_rag_chain(session_filter)

        with st.spinner("Searching KT knowledge base..."):
            chain, retriever = load_chain(session_filter)
            result = query_rag(chain, retriever, question, enable_guardrails=enable_guardrails)

        st.markdown("### Response")
        st.markdown(result["answer"])

        if enable_guardrails:
            st.divider()
            with st.expander("Guardrail Status Report", expanded=True):
                input_g = result.get("input_guardrail", {})
                output_g = result.get("output_guardrail", {})
                
                if input_g.get("passed"):
                    st.success(f"**Input Guardrail Passed**\n\n*Reason:* {input_g.get('reason')}")
                else:
                    st.error(f"**Input Guardrail Rejected**\n\n*Reason:* {input_g.get('reason')}")
                    
                if output_g.get("passed") is True:
                    st.success(f"**Output Guardrail Passed**\n\n*Reason:* {output_g.get('reason')}")
                elif output_g.get("passed") is False:
                    st.warning(f"**Output Guardrail Flagged (Potential Hallucination/Unfaithful)**\n\n*Reason:* {output_g.get('reason')}")
                elif output_g.get("passed") is None:
                    st.info(f"**Output Guardrail**\n\n*Status:* {output_g.get('reason')}")

        # if result["sources"]:
        #     st.divider()
        #     st.markdown("### Sources Used")
        #     for i, src in enumerate(result["sources"], 1):
        #         with st.expander(f"Source {i}: {src['source']} | {src['session']}"):
        #             st.write(f"**Session  :** {src['session']}")
        #             st.write(f"**Document :** {src['source']}")
        #             st.write(f"**Type     :** {src['doc_type']}")
        #             st.write(f"**Page     :** {src['page']}")

    elif ask_btn and not question.strip():
        st.warning("Please enter a question.")
    else:
        st.info("Select a session and ask a question on the left.")