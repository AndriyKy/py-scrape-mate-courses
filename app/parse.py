import asyncio
import time
from dataclasses import dataclass
from enum import Enum

from bs4 import BeautifulSoup
import fake_useragent
import aiohttp


BASE_URL = "https://mate.academy/"

headers = {"User-Agent": fake_useragent.UserAgent().random}


class CourseType(Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"


@dataclass
class Course:
    name: str
    short_description: str
    course_type: CourseType
    modules: str
    topics: str
    duration: str


async def get_url(extra_url: str = ""):
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL + extra_url, headers=headers) as page:
            return await page.text()


def pars_single_course(section) -> tuple:
    return (
        section.select_one("a")["href"],
        section.select_one("a").text,
        section.select_one("p").text,
    )


async def detailed_course_data(course_url: str) -> list:
    coro = await asyncio.create_task(get_url(course_url))
    soup = BeautifulSoup(coro, "lxml")

    div = soup.find_all(
        "p",
        attrs={"class": "typography_landingP2__KdC5Q CourseModulesHeading_text__EdrEk"},
    )

    return [p_tag.text for p_tag in div]


async def course_list_generator(soup, course_type) -> list[Course]:
    courses = []

    for section in soup:
        course_url, course_name, course_description = pars_single_course(section)
        course_data = await detailed_course_data(course_url)

        courses.append(
            Course(
                name=course_name,
                short_description=course_description,
                course_type=course_type,
                modules=course_data[0],
                topics=course_data[1],
                duration=course_data[2] if len(course_data) == 3 else "Невідома",
            )
        )

    return courses


async def get_all_courses() -> list[Course]:
    coro = await asyncio.create_task(get_url())
    soup = BeautifulSoup(coro, "html.parser")

    full_time = soup.select("#full-time section")
    part_time = soup.select("#part-time section")

    full_time_list = await course_list_generator(full_time, CourseType.FULL_TIME)
    part_time_list = await course_list_generator(part_time, CourseType.PART_TIME)
    full_time_list.extend(part_time_list)

    return full_time_list


if __name__ == "__main__":
    start = time.perf_counter()
    # rez = asyncio.run(get_all_courses())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    rez = asyncio.run(get_all_courses())
    # coro = loop.create_task(get_all_courses())
    # rez = loop.run_until_complete(asyncio.wait(coro))
    end = time.perf_counter()

    for course in rez:
        print(course)

    print("Elapsed:", end - start)
