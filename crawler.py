from typing import List, Tuple
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
from thefuzz import process

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"
}

total_regex = r"共有.*\n"
blank_regex = r"^\s*\n"
subst = ""


# Function to find the closest match in the 'Name' column
def fuzzy_search(
    query: str, choices: pd.Series, limit: int = 3
) -> List[Tuple[str, int, int]]:
    return process.extract(query, choices, limit=limit)


def fuzzy_search_on_column(
    query: str, df: pd.DataFrame, column: str, limit: int = 3
) -> pd.DataFrame:
    return pd.concat(
        [
            df.loc[key]
            for item, score, key in process.extract(query, df[column], limit=limit)
        ],
        axis=1,
    ).T
    # Include scores (but might be useless..)
    # items = []
    # for _, score, key in process.extract(query, df[column], limit=limit):
    #     # SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame
    #     # See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
    #     item = df.loc[key]
    #     item["score"] = score
    #     items.append(item)
    #
    # return pd.concat(items, axis=1).T


if __name__ == "__main__":
    res = requests.get("https://coolpc.com.tw/evaluate.php", headers=headers)
    soup = BeautifulSoup(res.text, "lxml")

    # with open("example.html", "r", encoding="utf-8") as fp:
    #     # BUG (solved by specifying encoding): *** UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 525: character maps to <undefined>
    #     soup = BeautifulSoup(fp.read(), "lxml")

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
    # BUG (solved): "formatted" HTML's new line character will influence parse result..
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
                        name_string = blank_result.split(",")[0].strip()
                        price_int = blank_result.split("$").pop().split(" ")[0].strip()

                        if price_int != "1":
                            all_items.append(
                                {
                                    "category": class_name,
                                    "type": subclass_name,
                                    "product": re.sub(r"\s+", " ", name_string),
                                    "price": int(price_int),
                                    "time": time_string,
                                }
                            )
    print(df := pd.DataFrame(all_items))
    df.to_csv("result.csv", index=False, encoding="utf-8")

    # Adhoc fix (TODO: improve this)
    # df['product'][df['product'].str.contains('宏')]
    # 32169    宏�猗cer Predator GM7000 2TB/Gen4/7400M/6700M/DR...
    # 32170    宏�猗cer Predator GM7000 4TB/Gen4/7400M/6700M/DR...
    # 37542    ACER 宏�� Predator Arc A770 16G(2400MHz/27cm/三年...
    # 37794    ACER 宏�� Predator Arc A770 16G(2400MHz/27cm/三年...
    # Name: product, dtype: object

    with open("result.csv", "r", encoding="utf-8") as fp:
        content = fp.read()
    with open("result.csv", "w", encoding="utf-8") as fp:
        fp.write(content.replace("宏��", "宏碁"))

    # Apply fuzzy search
    print(matches := fuzzy_search("4070 super", df["product"], limit=10))

    print(match_df := fuzzy_search_on_column("4060ti", df, "product", limit=10))

    import ipdb

    ipdb.set_trace()
