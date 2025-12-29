def get_questions(missing):
    questions = []

    if "hosts" in missing:
        questions.append("Please provide target IP addresses or subnet.")

    if "credentials" in missing:
        questions.append(
            "Please provide SSH username and authentication method "
            "(password or SSH key)."
        )

    return questions
