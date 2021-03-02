"""
Developer: I. Kosilov (100%)
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from prettytable import PrettyTable
from bs4 import BeautifulSoup
from requests import get


def get_qb_urls(url: str) -> list:
    """
    Функция принимает на вход url-адрес для какой-либо буквы латинского алфавита.
    Пример: https://www.nfl.com/players/active/c
    Далее парсит все ссылки на квотербеков и переходит к следующей странице для данного адреса
    (на ней тоже парсит квотербеков).
    :param url: url-адрес для какой-либо буквы латинского алфавита
    :return: ссылки на игроков кветербеков
    """
    qbs = []
    while True:
        try:
            response = get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            players_table = soup.find("tbody")
            players_info = players_table.find_all("tr")
            for player_info in players_info:
                if player_info.find_all("td")[2].text.strip() == "QB":
                    qbs.append(player_info.find("a").get("href"))
            url_suffix = soup.select("a.nfl-o-table-pagination__next")[0].get("href")
            url = f"https://www.nfl.com{url_suffix}"
        except IndexError:
            return qbs


def get_qb_metrics(relative_url: str) -> tuple:
    """
    Парсит метрики квотербека: name, ATT, COMP, YDS, TD, INT, PR, url
    :param relative_url: ссылка на квотербека
    :return: возращает метрики для данного квотербека
    """
    try:
        url = f"https://www.nfl.com{relative_url}stats/"
        response = get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        metrics = soup.find_all("tfoot")[0].find_all("th")
        metrics = [metric.text.strip() for metric in metrics]
        name = soup.select_one("figure.nfl-c-player-header__background").find("img").get("alt").strip()
        ATT, COMP, YDS, TD, INT, PR = metrics[3], metrics[4], metrics[6], metrics[9], metrics[10], metrics[-1]
        return name, ATT, COMP, YDS, TD, INT, PR, url
    except IndexError:
        url = f"https://www.nfl.com{relative_url}stats/"
        response = get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        name = soup.select_one("figure.nfl-c-player-header__background").find("img").get("alt").strip()
        return name, 0, 0, 0, 0, 0, 0, url


def main():
    """
    Функция делает запросы в потоках, так быстрее в 16 раз, чем в одно потоке.
    Среднее время выполнения программы = 1 минута.
    Программа возращает таблицу с квотербеками, красиво отформатированную с помощью модуля prettytable.
    :return: таблица с метриками квотербеков
    """
    with ThreadPoolExecutor() as pool:
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                   'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        start_urls = [f"https://www.nfl.com/players/active/{letter}" for letter in letters]
        future_qb_urls = [pool.submit(get_qb_urls, start_url) for start_url in start_urls]
        qb_urls = []
        for qb_url in as_completed(future_qb_urls):
            qb_urls += qb_url.result()
        future_qbs_metrics = [pool.submit(get_qb_metrics, url) for url in qb_urls]
        qbs_metrics = [qb_metrics.result() for qb_metrics in as_completed(future_qbs_metrics)]
    table = PrettyTable()
    table.field_names = ["Name", "ATT", "COMP", "YDS", "TD", "INT", "PR", "URL"]
    table.add_rows(qbs_metrics)
    return table


if __name__ == "__main__":
    print(main())
