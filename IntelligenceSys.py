from dotenv import load_dotenv

load_dotenv()

import os
import requests
from rich import print

from langchain.tools import tool

@tool
def get_weather(city : str) -> str:

    """ give me the present weather details of the give city """

    API_KEY = os.getenv("OPENWEATHER_API_KEY")

    if not API_KEY:
        return "API_KEY is not inserted"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        # print(data)
        if res.status_code != 200:
            return f'Error : {data.get("message", "could not fetch weather")}'


        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]

        return f"the weather in the {city}: {desc}, {temp} C"


    except requests.RequestException as e:
        return f"Error whille fetching weather:  {e}"


# print(get_weather.invoke("delhi"))


# news tool

from tavily import TavilyClient


@tool
def get_news(city : str) -> str:

    """Return the latest news of given city"""

    API_KEY = os.getenv("TAVILY_API_KEY")

    if not API_KEY:
        return "API_KEY is not set"

    tavily_client = TavilyClient(
        api_key=API_KEY,
        )

    try:
        res = tavily_client.search(
            query= f"latest news in {city}",
            search_depth="basic",
            max_results=4
        )

        # print(res)

        results = res.get("results", [])

        news_list = []

        for result in results:
            title = result.get('title', "No title")
            url = result.get('url', "")
            content = result.get('content', "")

            news_list.append(
                f"-{title}\n"
                f" {url}\n"
                f" {content[:200]}...."
            )

        return f"latest news in {city}:\n\n" + "\n\n".join(news_list)

    except Exception as e:
        return f"Error: {e}"

# print(get_news.invoke("delhi"))


from langchain_mistralai import ChatMistralAI
from langchain.messages import HumanMessage, ToolMessage

llm = ChatMistralAI(model_name= "mistral-small-2603")


tools = {
    "get_weather" : get_weather,
    "get_news" : get_news
}

llm_with_tools = llm.bind_tools(
    [get_weather, get_news]
)

messages = []

print("\nCity intelligence System")

print("Type exit to quit")

while True:

    user_input = input("YOU : ")

    if user_input.lower() == "exit":
        print("See you again")
        break


    messages.append(
        HumanMessage(content=user_input)
        )


    while True:

        result = llm_with_tools.invoke(messages)
        messages.append(result)

        if result.tool_calls:

            for tool_call in result.tool_calls:

                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                confirm = input(f"do you want confirm to excute {tool_name}. yes/no : ")

                if confirm.lower() != "yes":

                    print("Tool : tool access has denied, I can't not proceed without accepting confirm")
                    messages.append(
                        ToolMessage(
                            content=f"tool access has denied",
                            tool_call_id = tool_id
                            )
                    )
                    continue

                if tool_name not in tools:

                    print(f"tool is not avaiable right now")

                    messages.append(
                        ToolMessage(
                            content=f"unknown tool: {tool_name}",
                            tool_call_id = tool_id
                        )
                    )
                    continue

                tool_result = tools.get(tool_name).invoke(
                    tool_args
                )

                print(f"\nTool Results : \n{tool_result}")

                messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id = tool_id
                                )
                )

            continue


        else:
            print(f"AI : {result.content}")
            break



