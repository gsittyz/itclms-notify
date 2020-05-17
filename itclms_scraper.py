# まだまだ
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # , Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
import traceback
# import argparse
from collections import deque
from datetime import datetime as dt
import os

WAIT_TIME = 10
PASSWORD = os.environ["UT_PASS"]
USER_NAME = os.environ["UT_USER"]


def scrape():

    try:
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)

        # ITCLMSトップページ
        driver.get("https://itc-lms.ecc.u-tokyo.ac.jp/login")
        WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="com_auth"]/div/div/a')))
        driver.find_element_by_xpath('//*[@id="com_auth"]/div/div/a').click()

        # 組織アカウントログイン
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, 'userNameInput')))
        driver.find_element_by_id('userNameInput').send_keys(USER_NAME)
        driver.find_element_by_id('passwordInput').send_keys(PASSWORD)

        driver.find_element_by_id('submitButton').click()

        # LMS時間割画面
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[contains(@class, "course_on_timetable")]')))
        lecture_cells = driver.find_elements_by_xpath(
            '//div[contains(@class, "course_on_timetable")]')

        lecture_ids = deque([])

        for lecture_cell in lecture_cells:
            lecture_id = lecture_cell.get_attribute("id")
            if lecture_id in lecture_ids:
                continue
            else:
                lecture_ids.append(lecture_id)

        lecture_infos = deque([])
        for lecture_id in lecture_ids:
            driver.get(
                f"https://itc-lms.ecc.u-tokyo.ac.jp/lms/course?idnumber={lecture_id}"
            )
            WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.ID, 'courseName')))
            lecture_name = driver.find_element_by_xpath(
                '//*[@id="courseName"]/div[1]').text.split()[2]
            print(lecture_name)
            id_number = driver.find_element_by_xpath(
                '//*[@id="courseTopForm"]/input[1]').get_attribute("value")
            year = driver.find_element_by_xpath(
                '//*[@id="courseTopForm"]/input[2]').get_attribute("value")

            report_lines = driver.find_elements_by_xpath(
                "//div[contains(@class, 'report_list_line')]")
            report_infos = deque([])

            for report_line in report_lines:
                title = report_line.find_element_by_xpath(
                    './/div[contains(@class, "break")]').text
                time_start = report_line.find_element_by_xpath(
                    './/div[contains(@class, "timeStart")]').text
                time_start = dt.strptime(time_start, '%Y/%m/%d %H:%M')
                time_end = report_line.find_element_by_xpath(
                    './/div[contains(@class, "timeEnd")]').text
                time_end = dt.strptime(time_end, '%Y/%m/%d %H:%M')
                submit_status = report_line.find_element_by_xpath(
                    './/div[contains(@class, "submitStatus")]').text
                report_id = report_line.find_element_by_xpath(
                    './/input[contains(@class, "reportId")]').get_attribute(
                        "value")
                if len(
                        report_line.find_elements_by_xpath(
                            './/div[contains(@class, "result_list_btn")]')
                ) > 0:
                    edit = True
                else:
                    edit = False
                report_info = {
                    "title": title,
                    "time_start": time_start,
                    "time_end": time_end,
                    "submit_status": submit_status,
                    "report_id": report_id,
                    "edit": edit
                }
                report_infos.append(report_info)
            lecture_info = {
                "name": lecture_name,
                "id": id_number,
                "year": year,
                "report_infos": list(report_infos)
            }
            lecture_infos.append(lecture_info)

        return list(lecture_infos)

    except Exception:
        sys.stderr.write(traceback.format_exc())
    finally:
        driver.close()
        driver.quit()


def submit_check(lecture_infos):
    assignments = deque([(dt.now(), "現在時刻", "==================")])
    for lecture_info in lecture_infos:
        lecture_name = lecture_info["name"]
        # 提出可能な課題を検索する
        for report_info in lecture_info["report_infos"]:
            if report_info["submit_status"] == "未提出" and report_info["edit"]:
                time_end = report_info["time_end"]
                title = report_info["title"]
                assignments.append((time_end, lecture_name, title))
    return sorted(assignments)


def to_text(assignments):
    text_list = deque([])
    for assignment in assignments:
        text_list.append(
            f"{assignment[0].strftime('%m/%d %H:%M')}\n{assignment[1][:4]} {assignment[2]}"
        )
    return "\n\n".join(text_list)


if __name__ == "__main__":
    lecture_infos = scrape()
    for lecture_info in lecture_infos:
        print(lecture_info)
    assignments = submit_check(lecture_infos)
    for assignment in assignments:
        print(assignment)
    print(to_text(assignments))
    # google_task(lecture_infos)
    # google_task(None)
