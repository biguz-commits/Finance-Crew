from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, tool
from crewai.agents.agent_builder.base_agent import BaseAgent

from app.finance_crew.tools.researcher_agent import (
    ReadPortfolioTickersTool,
    FetchYFinancePricesTool,
    ComputeMarketMetricsTool,
)

from app.finance_crew.tools.risk_analyst import (
    BuildPortfolioReturnsTool,
    PortfolioRiskMetricsTool,
    ExposuresVsTargetTool,
    ConcentrationMetricsTool,
    BetaCorrelationTool,
    DataQualityCheckTool,
)


@CrewBase
class FinAssistCrew():
    """FinAssist crew: Market Data → Risk → Rebalance+Report"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @tool
    def read_portfolio_tickers_tool(self) -> ReadPortfolioTickersTool:
        return ReadPortfolioTickersTool()

    @tool
    def fetch_yfinance_prices_tool(self) -> FetchYFinancePricesTool:
        return FetchYFinancePricesTool()

    @tool
    def compute_market_metrics_tool(self) -> ComputeMarketMetricsTool:
        return ComputeMarketMetricsTool()

    @tool
    def build_portfolio_returns_tool(self) -> BuildPortfolioReturnsTool:
        return BuildPortfolioReturnsTool()

    @tool
    def portfolio_risk_metrics_tool(self) -> PortfolioRiskMetricsTool:
        return PortfolioRiskMetricsTool()

    @tool
    def exposures_vs_target_tool(self) -> ExposuresVsTargetTool:
        return ExposuresVsTargetTool()

    @tool
    def concentration_metrics_tool(self) -> ConcentrationMetricsTool:
        return ConcentrationMetricsTool()

    @tool
    def beta_correlation_tool(self) -> BetaCorrelationTool:
        return BetaCorrelationTool()

    @tool
    def data_quality_check_tool(self) -> DataQualityCheckTool:
        return DataQualityCheckTool()

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],  # type: ignore[index]
            verbose=True,
            tools=[
                self.read_portfolio_tickers_tool,
                self.fetch_yfinance_prices_tool,
                self.compute_market_metrics_tool,
            ],
        )

    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_analyst'],  # type: ignore[index]
            verbose=True,
            tools=[
                self.build_portfolio_returns_tool,
                self.portfolio_risk_metrics_tool,
                self.exposures_vs_target_tool,
                self.concentration_metrics_tool,
                self.beta_correlation_tool,
                self.data_quality_check_tool,
            ],
        )

    @agent
    def rebalancer(self) -> Agent:
        return Agent(
            config=self.agents_config['rebalancer'],  # type: ignore[index]
            verbose=True,
            tools=[],
        )

    @task
    def market_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['market_data_task'],  # type: ignore[index]
        )

    @task
    def risk_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['risk_analysis_task'],  # type: ignore[index]
        )

    @task
    def rebalancing_and_reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['rebalancing_and_reporting_task'],  # type: ignore[index]
            output_file='output/report.md',
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
