import chromadb


client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="project_memory"
)


def save_project_memory(
    project_name,
    architecture_report,
    technical_debt_report,
    risk_report,
    recommendation_report
):

    memory_text = f"""

Project:
{project_name}

Architecture Report:
{architecture_report}

Technical Debt Report:
{technical_debt_report}

Risk Report:
{risk_report}

Recommendation Report:
{recommendation_report}

"""

    try:

        collection.delete(
            ids=[project_name]
        )

    except:

        pass

    collection.add(

        documents=[
            memory_text
        ],

        ids=[
            project_name
        ]

    )


def get_project_memory(
    project_name
):

    result = collection.get(
        ids=[project_name]
    )

    return result


def search_project_memory(
    question
):

    result = collection.query(

        query_texts=[
            question
        ],

        n_results=1

    )

    return result