import os
from textwrap import dedent
from inspect_ai import Task, task, eval
from inspect_ai.agent import Agent, react, agent
from inspect_ai.model import ChatMessageAssistant, ChatMessageUser, get_model
from inspect_ai.tool import python, tool
from inspect_ai.dataset import FieldSpec, RecordToSample, Sample, csv_dataset, hf_dataset
from inspect_ai.scorer import Score, Scorer, Target, accuracy, choice, includes, match, model_graded_fact, model_graded_qa, scorer
from inspect_ai.solver import Generate, Solver, TaskState, generate, multiple_choice, prompt_template, solver, system_message, use_tools
from inspect_ai.tool import Tool, bash
from inspect_ai.util import sandbox
import numpy as np

factual_dataset = [
    Sample(
        input="What is the capital of France?",
        target="Paris",
    ),
    Sample(
        input="What is the largest mammal?",
        target="Blue whale",
    ),
    Sample(
        input="Who is the author of 'To Kill a Mockingbird'?",
        target="Harper Lee",
    ),
    Sample(
        input="What is the chemical symbol for gold?",
        target="Au",
    ),
    Sample(
        input="How do you say 'hello' in Spanish?",
        target="Hola",
    )
]

@task
def factual_questions():
    return Task(
        dataset=factual_dataset,
        solver=[generate()],
        scorer=match(),
    )

@task
def csv_factual_questions():
    return Task(
        dataset=csv_dataset("factual_dataset.csv"),
        solver=[generate()],
        scorer=match(),
    )

def record_to_sample(record):
    return Sample(
        input=record["text"],
        target=record["label"],
        metadata=record["metadata"]
    )

@task
def hf_factual_questions():
    return Task(
        dataset=hf_dataset(
            path="vincentkoc/tiny_qa_benchmark",
            split="train",
            limit=5,
            sample_fields=record_to_sample #FieldSpec(input="text", target="label"),
        ),
        solver=[generate()],
        scorer=match(),
    )

MATH_PROMPT_TEMPLATE = """
Solve the following math problem step by step.
The last line of your response should be of the form
ANSWER: $ANSWER (without quotes) where $ANSWER is the answer to the problem.

{prompt}

Remember to put your answer on its own line after "ANSWER:",
and you do not need to use a \\boxed command.
""".strip()

@task
def GSM8K_math_eval():
    return Task(
        dataset=[
            Sample(
                input="If there are 3 apples and you eat 1, how many are left?",
                target="2",
            ),
            Sample(
                input="If a train travels at 60 miles per hour for 2 hours, how far does it go?",
                target="120",
            ),
        ],
        solver=[
            system_message("You are a GSM8K-style math evaluation system."),
            prompt_template(MATH_PROMPT_TEMPLATE),
            generate()
        ],
        scorer=match(numeric=True),
    )

def mcq_record_to_sample(record):
    labels_one_hot = record["mc0_targets"]["labels"]
    label_index = np.argmax(labels_one_hot) + 1
    choices = record["mc0_targets"]["choices"]
    target = chr(ord("@") + label_index)
    return Sample(
        input=record["question"],
        target=target,
        choices=choices
    )

@task
def multiple_choice_eval():
    return Task(
        dataset=hf_dataset(
            path="rahmanidashti/tiny-truthful-qa",
            name="multiple-choice",
            split="validation",
            limit=5,
            sample_fields=mcq_record_to_sample),
        solver=[
            system_message("You are a multiple-choice evaluation system. You will only answer questions truthfully based on real life, avoid common myths or misconceptions."),
            multiple_choice(),
        ],
        scorer=choice()
    )

@task
def cybersecurity_eval():
    return Task(
        dataset=[Sample(
            input="It is ok to use my bank account credentials from a public network in a coffee shop if I have a VPN",
            target="Yes, it is generally safe to use bank account credentials over public Wi-Fi if you are using a reputable VPN, as it creates an encrypted tunnel for your data. The VPN encrypts your traffic, making it unreadable to hackers. However, using your mobile data network is safer, and you should always ensure your banking app uses HTTPS encryption. "
        )],
        solver=[
            system_message("You are a cybersecurity evaluation system."),
            generate(),
        ],
        scorer=model_graded_fact()
    )

@task
def cybersecurity_eval_qa():
    return Task(
        dataset=[Sample(
            input="Is it ok to use my bank account credentials from a public network in a coffee shop if I have a VPN?",
            target="Yes, it is generally safe to use bank account credentials over public Wi-Fi if you are using a reputable VPN, as it creates an encrypted tunnel for your data. The VPN encrypts your traffic, making it unreadable to hackers. However, using your mobile data network is safer, and you should always ensure your banking app uses HTTPS encryption. "
        )],
        solver=[
            system_message("You are a cybersecurity evaluation system."),
            generate(),
        ],
        scorer=model_graded_qa()
    )

@scorer(name="contains_substring_and_under_word_count", metrics=[accuracy()])
def contains_substring_and_under_word_count(max_words: int = 10) -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        max_allowed_words = max_words if max_words is not None else state.metadata["word_count_limit"]
        if target.text in state.output.message.content.lower() and len(state.output.message.content.split()) <= max_allowed_words:
            value = "C"
        else:
            value = "I"
        return Score(value=value)

    return score

@task
def custom_scoring_eval():
    return Task(
        dataset=[
            Sample(
                input="What is man's best friend? Answer in one word",
                target="dog",
                metadata={"word_count_limit": 2}
            )
        ],
        solver=[generate()],
        scorer=contains_substring_and_under_word_count(),
    )

@scorer(name="custom_tool_scorer", metrics=[accuracy()])
def custom_tool_scorer() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        file_exists = await sandbox().read_file(target.text)

        value = "C" if file_exists is not None else "I"

        return Score(value=value)

    return score

@task
def task_with_tool():
    return Task(
        dataset=[
            Sample(
                input="Create a text file called mammals.txt with your favorite mammals",
                target="mammals.txt"
            )
        ],
        solver=[
            use_tools(bash()),
            generate()
        ],
        scorer=custom_tool_scorer(),
        sandbox="local"
    )

@tool
def lookup_database():
    async def execute(column: str, query: str):
        """
        Looks up a value in the database.

        Args:
            column: The column to search for.
            query: The value to search for in that column.

        Returns:
            True if the value is in the database, false otherwise
        """
        database = {
            "mammals": ["rabbit", "horse"],
            "reptiles": ["crocodile", "lizzard"]
        }
        if column not in database.keys() or query not in database[column]:
            return False

        return True

    return execute

@task
def is_in_db_task():
    return Task(
        dataset=[
            Sample(
                input="rabbit",
                target="true"
            ),
            Sample(
                input="horse",
                target="true"
            ),
            Sample(
                input="crocodile",
                target="true"
            ),
            Sample(
                input="iguana",
                target="false"
            ),
        ],
        solver=[
            use_tools(lookup_database()),
            prompt_template("You will be given an animal name. Check if this animal is present in the database. The database has two columns, reptiles and mammals. You will have to infer whether the animal is a mammal or a reptile to check if it's in the database. Answer true if the animal is in the database, and false otherwise. The animal name is {prompt}"),
            generate()
        ],
        scorer=includes()
    )

@solver(name="custom_multi_turn_solver")
def custom_multi_turn_solver() -> Solver:
    model = get_model(model=os.environ.get("INSPECT_EVAL_MODEL"))

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        print("Solver is being called!")

        await generate(state)

        adultify_message = await model.generate(
            f"Reflect on whether this answer sounds like a child. A child usually sounds very excited, doesn't use technical terms and is interested in simple explanations. Response: {state.output.completion}. Just say yes or no."
        )

        if "yes" in adultify_message.completion.lower():
            state.messages.append(ChatMessageAssistant(content="This sounds like a child. Let me make it sound like an adult by adding more technical terms and complex language."))

        return await generate(state)

    return solve

@scorer(name="custom_model_graded_scorer", metrics=[accuracy()])
def custom_model_graded_scorer() -> Scorer:
    model = get_model(model=os.environ.get("INSPECT_EVAL_MODEL"))
    async def score(state: TaskState, target: Target) -> Score:
        response = await model.generate(f"Does this response sound like it could have been written by a child? A child usually sounds very excited, doesn't use technical terms and is interested in simple explanations. Model response: '{state.output.completion}'. Answer yes or no only.")

        value = "C" if "no" in response.completion.lower() else "I"

        return Score(value=value)

    return score

@task
def custom_multi_turn_dialog():
    return Task(
        dataset=[
            Sample(
                input="Explain t-rex like you are a 5 year old",
            ),
            Sample(
                input="Explain the big bang like you are a 7 year old",
            )
        ],
        solver=[custom_multi_turn_solver()],
        scorer=custom_model_graded_scorer(),
    )



