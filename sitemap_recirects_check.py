import os
from pathlib import Path
import requests
from lxml import etree

sitemaps = [
    "PUT_YOUR_SITEMAP_HERE.XML",
]


def check_sitemap_urls(sitemap, limit=50):
    """Attempts to resolve all urls in a sitemap and returns the results

    Args:
        sitemap (str): A URL
        limit (int, optional): The maximum number of URLs to check. Defaults to 50.
            Pass None for no limit.

    Returns:
        list of tuples: [(status_code, history, url, msg)].
            The history contains a list of redirects.
    """
    results = []
    name = os.path.basename(sitemap).split(".")[0]
    res = requests.get(sitemap)
    doc = etree.XML(res.content)

    # xpath query for selecting all element nodes in namespace
    query = "descendant-or-self::*[namespace-uri()!='']"
    # for each element returned by the above xpath query...
    for element in doc.xpath(query):
        # replace element name with its local name
        element.tag = etree.QName(element).localname

    # get all the loc elements
    links = doc.xpath(".//loc")
    for i, link in enumerate(links, 1):
        try:
            url = link.text
            print(f"{i}. Checking {url}")
            r = requests.get(url)

            if r.history:
                result = (
                    r.status_code,
                    r.history,
                    url,
                    "No error. Redirect to " + r.url,
                )
            elif r.status_code == 200:
                result = (r.status_code, r.history, url, "No error. No redirect.")
            else:
                result = (r.status_code, r.history, url, "Error?")
        except Exception as e:
            result = (0, [], url, e)

        results.append(result)

        if limit and i >= limit:
            break

    # Sort by status and then by history length
    results.sort(key=lambda result: (result[0], len(result[1])))

    return results


def main():
    for sitemap in sitemaps:
        results = check_sitemap_urls(sitemap)

        name = os.path.basename(sitemap).split(".")[0]
        report_path = Path(f"{name}.txt")
        report = f"{sitemap}\n\n"

        # 301s - may want to clean up 301s if you have multiple redirects
        report += "301s\n"
        i = 0
        for result in results:
            if len(result[1]):  # history
                i += 1
                report += f"{i}. "
                for response in result[1]:
                    report += f">> {response.url}\n\t"
                report += f">>>> {result[3]}\n"

        # non-200s
        report += "\n\n==========\nERRORS\n"
        for result in results:
            if result[0] != 200:
                report += f"{result[0]} - {result[2]}\n"

        report_path.write_text(report)

main()
