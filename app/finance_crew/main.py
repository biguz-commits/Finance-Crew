import sys
import warnings
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from app.finance_crew.crew import FinAssistCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the FinAssist crew.
    """
    inputs = {
        "topic": "Portfolio Management",
        "current_year": str(datetime.now().year),
        "dataset_path": "data/portfolio_large.csv",
    }

    try:
        FinAssistCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the FinAssist crew for a given number of iterations.
    """
    inputs = {
        "topic": "Risk Analysis",
        "current_year": str(datetime.now().year)
    }

    try:
        FinAssistCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the FinAssist crew execution from a specific task.
    """
    try:
        FinAssistCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


if __name__ == "__main__":
    run()
