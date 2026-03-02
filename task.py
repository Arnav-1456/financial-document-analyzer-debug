## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, read_data_tool

## Creating a task to help solve user's query
analyze_financial_document_task = Task(
    description="Analyze the financial document at '{file_path}' thoroughly to answer the user's query: {query}\n\
Read the document using the provided tool and extract key financial metrics including revenue, \
net income, operating margins, cash flow, debt levels, and any other relevant data points.\n\
Provide a structured, data-driven analysis that directly addresses the user's question.\n\
Identify notable trends, year-over-year changes, and significant financial events.\n\
Support all claims with specific numbers and page references from the document.",

    expected_output="""A comprehensive financial analysis report containing:
1. Executive Summary — key findings in 2-3 sentences
2. Key Financial Metrics — revenue, net income, EPS, margins, cash flow (with exact figures)
3. Trend Analysis — year-over-year or quarter-over-quarter changes
4. Notable Items — significant events, risks, or opportunities mentioned in the document
5. Data Sources — specific references to sections/pages of the document analyzed""",

    agent=financial_analyst,
    tools=[read_data_tool],
    async_execution=False,
)

## Creating an investment analysis task
investment_analysis = Task(
    description="Based on the financial analysis from the document at '{file_path}', provide well-reasoned investment recommendations.\n\
Consider the financial health indicators, growth trajectory, competitive positioning, \
and current market conditions relevant to the company.\n\
User's specific query: {query}\n\
Evaluate both opportunities and risks before making any recommendations.\n\
Ensure all recommendations comply with standard investment advisory practices.",

    expected_output="""A structured investment analysis containing:
1. Investment Thesis — clear bull and bear cases supported by financial data
2. Valuation Assessment — whether the company appears undervalued, fairly valued, or overvalued
3. Key Investment Metrics — P/E ratio, P/B ratio, dividend yield, growth rates (where available)
4. Recommendations — specific, actionable investment guidance with clear rationale
5. Risk Factors — key risks that could affect the investment thesis
6. Disclaimer — standard investment advisory disclaimer""",

    agent=investment_advisor,
    tools=[read_data_tool, search_tool],
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description="Conduct a thorough risk assessment based on the financial document at '{file_path}'.\n\
Identify and categorize all material risks: market risk, credit risk, operational risk, \
liquidity risk, regulatory risk, and any company-specific risks.\n\
User's query context: {query}\n\
Quantify risks where possible using data from the financial document.\n\
Propose specific, practical risk mitigation strategies for each identified risk.",

    expected_output="""A comprehensive risk assessment report containing:
1. Risk Summary — overview of the company's overall risk profile
2. Risk Categories — detailed breakdown by risk type (market, credit, operational, liquidity, regulatory)
3. Risk Quantification — severity ratings and potential financial impact where measurable
4. Key Risk Indicators — specific metrics or warning signs from the financial data
5. Mitigation Strategies — practical recommendations to address each major risk
6. Risk Monitoring — suggested KPIs and thresholds for ongoing risk monitoring""",

    agent=risk_assessor,
    tools=[read_data_tool, search_tool],
    async_execution=False,
)

## Creating a document verification task
verification = Task(
    description="Verify that the uploaded document at '{file_path}' is a legitimate financial document.\n\
Check for the presence of standard financial report elements: income statement, \
balance sheet, cash flow statement, management discussion, notes to financial statements.\n\
Identify the company name, reporting period, document type (10-K, 10-Q, annual report, etc.), \
and any filing metadata.",

    expected_output="""A verification report containing:
1. Document Type — identified type of financial document
2. Company Information — company name, ticker symbol (if available), reporting period
3. Document Completeness — which standard financial sections are present
4. Authenticity Assessment — confidence level that this is a genuine financial document
5. Key Metadata — filing date, auditor, any regulatory references""",

    agent=verifier,
    tools=[read_data_tool],
    async_execution=False,
)