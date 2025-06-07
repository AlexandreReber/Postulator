from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

## Load environment variables ##
import os
from dotenv import load_dotenv
load_dotenv(".env")

import streamlit as st
os.environ["SERPER_API_KEY"] = st.secrets["serper_api_key"]

## Load tools ##
from crewai_tools import (
  FileReadTool,
  ScrapeWebsiteTool,
  MDXSearchTool,
  SerperDevTool,
)
from src.postulator.tools.custom_tool import human_feedback, final_response_cleaner, PdfReaderTool, cv_final_response_cleaner

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()
read_file = FileReadTool()
read_pdf = PdfReaderTool()
read_resume_template = FileReadTool(file_path='input/resume_template.tex')
response_cleaner_md = final_response_cleaner(strings_to_remove=["```md", "```markdown", "```", "'''md", "'''markdown", "'''"], result_as_answer=True)
read_motivation_letter_example = FileReadTool(file_path='input/example_motivation_letter.txt')

@CrewBase
class Postulator():
	"""Postulator crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, llm_key, cv_path) -> None:
		super().__init__()
		self.cv_path = cv_path
		self.llm = LLM(
					model=os.environ["MODEL"], 
					api_key=llm_key,
					temperature=0.0,
					)
		self.llm_creative = LLM(
					model=os.environ["MODEL"],
					api_key=llm_key,
					temperature=0.1,
					)
		self.read_resume = FileReadTool(file_path=self.cv_path)
		self.semantic_search_resume = MDXSearchTool(
			mdx=self.cv_path,
			config=dict(
				llm=dict(
					provider="google",
					config=dict(
						model="gemini/gemini-1.5-flash",
						api_key=llm_key,
					),
				),
				embedder=dict(
					provider="google",
					config=dict(
						model="models/embedding-001",
						task_type="retrieval_document",
					),
				),
			)
		)

	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			tools = [scrape_tool, search_tool, read_file, read_pdf],
			verbose=True,
			llm = self.llm,
			max_retry_limit=10
		)
	
	@agent
	def profile_matcher(self) -> Agent:
		return Agent(
			config=self.agents_config['profile_matcher'],
			tools = [],
			verbose=True,
			llm = self.llm,
			max_retry_limit=10
		)
	
	@agent
	def resume_strategist(self) -> Agent:
		return Agent(
			config=self.agents_config['resume_strategist'],
			tools = [scrape_tool,
					 read_resume_template,
					 response_cleaner_md,
					 ],
			verbose=True,
			llm = self.llm,
			max_retry_limit=10
		)
	
	@agent
	def motivation_specialist(self) -> Agent:
		return Agent(
			config=self.agents_config['motivation_specialist'],
			tools = [read_motivation_letter_example,
					 human_feedback(),
					],
			verbose=True,
			llm = self.llm_creative,
			max_retry_limit=10,
		)

	@task
	def research_task(self) -> Task:
		return Task(
			config=self.tasks_config['research_task'],
			context=[],
			max_retries=10,
		)
	
	@task
	def strength_weakness_analysis_task(self) -> Task:
		return Task(
			config=self.tasks_config['strength_weakness_analysis_task'],
			context=[self.research_task()],
			max_retries=10,
		)

	@task
	def resume_strategy_task(self) -> Task:
		return Task(
			config=self.tasks_config['resume_strategy_task'],
			output_file="output/tailored_resume.md",
    		context=[self.research_task(), self.strength_weakness_analysis_task()],
			max_retries=10,
		)

	@task
	def motivation_letter_task(self) -> Task:
		return Task(
			config=self.tasks_config['motivation_letter_task'],
			output_file="output/motivation_letter.json",
    		context=[self.research_task(), self.resume_strategy_task(), self.strength_weakness_analysis_task()],
			max_retries=10,
		)
	
	@crew
	def crew(self) -> Crew:
		"""Creates the Postulator crew"""

		return Crew(
			agents= [ self.researcher(), 
					  self.profile_matcher(), 
					  self.resume_strategist(),
					  self.motivation_specialist(),
					],
			tasks= [self.research_task(),
		   			self.strength_weakness_analysis_task(),
					self.resume_strategy_task(),
					self.motivation_letter_task(),
					],
			process=Process.sequential,
			verbose=True,
			max_rpm=15,
			chat_llm="gemini/gemini-2.0-flash",
		)



@CrewBase
class CVParser():
	"""CVParser crew"""

	agents_config = 'config/parser_agent.yaml'
	tasks_config = 'config/parser_task.yaml'

	def __init__(self, llm_key) -> None:
		super().__init__()
		self.llm = LLM(
					model=os.environ["MODEL"], 
					api_key=llm_key,
					temperature=0.0,
					)

	@agent
	def cv_parser(self) -> Agent:
		return Agent(
			config= self.agents_config['cv_parser'],
			tools = [cv_final_response_cleaner()],
			verbose=True,
			llm = self.llm,
			max_retry_limit=10
		)

	@task
	def cv_parser_task(self) -> Task:
		return Task(
			config=self.tasks_config['cv_parser_task'],
			context=[],
			max_retries=10,
		)
	
	@crew
	def crew(self) -> Crew:
		"""Creates the Postulator crew"""

		return Crew(
			agents= self.agents, # Automatically created by the @agent decorator
			tasks= self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			max_rpm=15,
		)
