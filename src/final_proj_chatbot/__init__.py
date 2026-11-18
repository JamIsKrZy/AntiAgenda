import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Power Scaling ❤️‍🔥❤️‍🔥❤️‍🔥", layout="centered")
    from final_proj_chatbot.routes import ALL_PAGES

    navigation = st.navigation(ALL_PAGES, position="top")
    navigation.run()


if __name__ == "__main__":
    main()