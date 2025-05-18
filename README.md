# Thu Dau Mot University GenAI workshop

Create by: Tony Do
E-mail: vanhuong.robotics@gmail.com
Date: 2025.05.18

## Instruction

Run AI Agent to work as math professor
	$ python math_professor.py

Run AI Agent to crawl paper in arxiv by date time 
1. Runn server LLM model in local
	$ ./serve_mistral_model_llm.sh
2. Execute script Agent:
	$python arxiv_crew.py --date <date time> --output <expect name>.html
		Arguments:
			- Date formate: date-month-year
			- Output format HTML: *.html
	Ex: $ python arxiv_crew.py --date 04-03-2025 --output tmp.html


