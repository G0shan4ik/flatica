import asyncio
import time

from playwright.async_api import async_playwright

from loguru import logger
from random import randint

import os
from datetime import datetime
from openpyxl import Workbook

from .cache_core import CacheCore


START_URL = "https://xn--80az8a.xn--d1aqf.xn--p1ai/сервисы/единый-реестр-застройщиков?objStatus=0%3A1%3A2"

API_URL_BASE = (
    "https://xn--80az8a.xn--d1aqf.xn--p1ai/"
    "%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%8B/api/erz/main/filter?"
    "sortField=devShortNm&sortType=asc&objStatus=0:1:2"
)

ITEMS_PER_PAGE = 10


async def main(error_mass: list[str] = None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Заходим на стартовую страницу
        await page.goto(START_URL)

        # 2. Читаем количество страниц с помощью XPath
        pages_text = await page.locator(
            'xpath=//*[@id="__next"]/div[2]/div[2]/div/div/div/div/div[2]/div[1]/div[2]/div[1]/p'
        ).inner_text()

        import re
        total_offsets = int(int(re.sub(r"\D", "", pages_text))/10) * 10
        logger.success("Total Offset:", total_offsets)

        # 3. Сбор данных со всех страниц
        cch = CacheCore()
        if error_mass:
            for url in error_mass:
                cch.delete_data(url=url)

        for offset in range(0, total_offsets + 10, 10):
            try:
                api_url = f"{API_URL_BASE}&offset={offset}&limit={ITEMS_PER_PAGE}"
                if api_url in cch.get_all_urls():
                    logger.warning(f"Already exists; \nOffset - {offset}/{total_offsets + 10}; URL ==>  {api_url}\n")
                    continue

                logger.info(f"Offset - {offset}/{total_offsets+10}; URL ==>  {api_url}")

                # Выполняем запрос через браузер — CORS и Referer обходятся
                _data = await page.evaluate(
                    f"""async () => {{
                        const response = await fetch("{api_url}");
                        return await response.json();
                    }}"""
                )
                cch.add_unique_data(
                    url=api_url,
                    data=_data
                )
                time.sleep(0.5)
            except Exception as ex:
                logger.error(f'Offset ERROR; EX_NAME ==> {ex}')
        print('\n\n\n')
        logger.success("=== ВСЕ ДАННЫЕ ПОЛУЧЕНЫ ===")
        logger.success(f"Всего элементов: {cch.get_len_cache()}")

        await browser.close()


def form_data() -> list[dict]:
    result_data: list[dict] = []
    error_urls: list[str] = []
    cch = CacheCore()
    cnt = 0
    for dct in cch.get_full_cache_info():
        cnt += 1
        logger.success(f'Start Format Stack == {cnt}')
        for k, v in dct.items():
            try:
                _json = v['data']['developers']
                for item in _json:
                    result_data.append(
                        {
                            "Регион регистрации": item.get('regRegionDesc', '-'),
                            "Краткое наименование": item.get('devShortCleanNm', '-'),
                            "Полное наименование": item.get('devFullCleanNm', '-'),
                            "Группа компаний": item.get('developerGroupName', '-'),
                            "Телефон": item.get('devPhoneNum', '-'),
                            "Email": item.get('devEmail', '-'),
                            "Сайт": item.get('devSite', '-'),
                            "ИНН": item.get('devInn', '-'),
                            "ОГРН": item.get('devOgrn', '-'),
                            "КПП": item.get('devKpp', '-'),
                            "Юридический адрес": item.get('devLegalAddr', '-'),
                            "Фактический адрес": item.get('devFactAddr', '-'),
                            "Проблемные объекты": item.get('problObjCnt', '-'),
                            "Объекты в строительстве": item.get('buildObjCnt', '-'),
                            "Сданные объекты": item.get('comissObjCnt', '-'),
                            "Фонд гарантирования": item.get('fundGuarantyFlg', '-'),
                            "Эскроу-счета": item.get('objGuarantyEscrowFlg', '-'),
                            "Господдержка": item.get('govFundFlg', '-'),
                        }
                    )
            except Exception as ex:
                error_urls.append(k)
                logger.error(f'ERROR FORMAT; URL == {k}; \nEX ==> {ex}')
    print('\n\n\n\n')
    if error_urls:
        logger.warning(f'ERROR URLS (len={len(error_urls)})')
        print('\n\n')
        print(error_urls)
        print('\n\n')
    logger.success(f'ALL Items COUNT = {len(result_data)}')
    return result_data


def get_xlsx(data: list[dict]):
    # 1. Путь к папке "all_data"
    folder_path = os.path.join(os.getcwd(), "all_data")
    os.makedirs(folder_path, exist_ok=True)

    # 2. Имя файла
    date_str = datetime.now().strftime("%d_%m_%Y")
    file_name = f"flatica_{date_str}.xlsx"
    file_path = os.path.join(folder_path, file_name)

    # 3. Создаём Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "data"

    if not data:
        wb.save(file_path)
        return file_path

    headers = list(data[0].keys())
    ws.append(headers)

    for item in data:
        row = [item.get(col, "") for col in headers]
        ws.append(row)

    wb.save(file_path)
    logger.success(f'CREATE XLSX  name == {file_name}')
    return file_path
