from bs4 import BeautifulSoup
import requests
import re
import textwrap
import pandas as pd

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"
}

total_regex = r"共有.*\n"
blank_regex = r"^\s*\n"
subst = ""


def wrap(string: str, length: int = 90) -> str:
    return "\n".join(textwrap.wrap(string, length))


if __name__ == "__main__":
    res = requests.get("https://coolpc.com.tw/evaluate.php", headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    time_string = ""

    all_items = []

    # Extracting the time from the page
    time_element = soup.find(id="Mdy")
    if time_element:
        time_string = time_element.text[:-2]

    # Loop through all rows in the tbody
    for row in soup.select("#tbdy > tr"):
        class_name = row.select_one("td.t").get_text(
            strip=True
        )  # Extract the class string
        select_element = row.select_one("td:nth-child(3) > select")

        if select_element:
            for option in select_element.find_all("option", value=True, disabled=False):
                # Clean the option text
                total_result = re.sub(total_regex, subst, option.text, 0, re.MULTILINE)
                blank_result = re.sub(blank_regex, subst, total_result, 0, re.MULTILINE)

                if len(blank_result) != 0:
                    name_string = blank_result.split(",")[0]
                    price_int = blank_result.split("$").pop().split(" ")[0]

                    if price_int != "1":
                        all_items.append(
                            {
                                "product": wrap(name_string),
                                "type": wrap(class_name),
                                "price": price_int,
                                "time": time_string,
                            }
                        )
    print(df := pd.DataFrame(all_items))
    df.to_csv("result.csv", index=False)
    import ipdb

    ipdb.set_trace()
