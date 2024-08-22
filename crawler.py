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

    # with open("example.html", "r") as fp:
    #     # *** UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 525: character maps to <undefined>
    #     soup2 = BeautifulSoup(fp.read(), "lxml")

    # BUG: got some weird Traditional Chinese character (the website default encoding is Big5)
    # e.g. 宏�� Acer, Acer宏��

    # # Check for meta charset
    # meta_tag = soup.find("meta", charset=True)
    # if meta_tag:
    #     res.encoding = meta_tag["charset"]
    # else:
    #     # Check for meta http-equiv content-type
    #     meta_tag = soup.find("meta", attrs={"http-equiv": "Content-Type"})
    #     if meta_tag and "charset=" in meta_tag["content"]:
    #         res.encoding = meta_tag["content"].split("charset=")[-1].strip()
    #     else:
    #         # Fallback to apparent encoding if no meta tag found
    #         res.encoding = res.apparent_encoding
    #
    # # UnicodeDecodeError: 'big5' codec can't decode byte 0xf9 in position 129275: illegal multibyte sequence
    # soup = BeautifulSoup(
    #     res.content.decode("Big5", errors="ignore").encode("utf-8"), "lxml"
    # )

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
            for optgroup in select_element.find_all("optgroup"):
                subclass_name = optgroup.get(
                    "label"
                )  # Extract the subclass name from the optgroup label

                for option in optgroup.find_all("option", value=True, disabled=False):
                    # Clean the option text
                    total_result = re.sub(
                        total_regex, subst, option.text, 0, re.MULTILINE
                    )
                    blank_result = re.sub(
                        blank_regex, subst, total_result, 0, re.MULTILINE
                    )

                    if len(blank_result) != 0:
                        name_string = blank_result.split(",")[0]
                        price_int = blank_result.split("$").pop().split(" ")[0]

                        if price_int != "1":
                            all_items.append(
                                {
                                    "category": wrap(class_name),
                                    "type": wrap(subclass_name),
                                    "product": wrap(name_string),
                                    "price": price_int,
                                    "time": time_string,
                                }
                            )
    print(df := pd.DataFrame(all_items))
    df.to_csv("result.csv", index=False, encoding="utf-8")

    # Adhoc fix
    with open("result.csv", "r", encoding="utf-8") as fp:
        content = fp.read()
    with open("result.csv", "w", encoding="utf-8") as fp:
        fp.write(content.replace("宏��", "宏碁"))

    import ipdb

    ipdb.set_trace()
