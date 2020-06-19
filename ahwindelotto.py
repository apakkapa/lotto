"""
usage:
    python ahwindelotto.py

    tells user if lotto won
    given the draw number
    and the number chosen

overview:

"""
from bs4 import BeautifulSoup
import requests

MAX_LOTTO_NUM = 36
QUERY_STR = 'http://www.nlcbplaywhelotto.com/nlcb-lotto-plus-results/?drawnumber={}'
CROSS = 'x'
CHECK_MARK = u'\u2713'


def main():
    drawnumber = get_draw()
    my_numbers = get_my_numbers()
    # print(my_numbers)
    query = QUERY_STR.format(drawnumber)

    response = requests.get(query)
    # response = '<Response object with lots of goodies, including a website's text>'

    html = response.text

    soup = BeautifulSoup(html, 'lxml')
    # draw_date = soup.find('div', 'drawDetails').div.text
    # jackpot = soup.find(id='jackpot').text
    numbers = soup.find_all("div", {"class": "lotto-balls"})
    winning_numbers = [number.text for number in numbers]
    powerball = soup.find('div', {"class": "ball yellow-ball"}).text
    winning_numbers.append('P' + powerball)
    # print(winning_numbers)

    win_dict = check(winning_numbers, my_numbers)
    # print(win_dict)
    won = False not in win_dict.values()

    if won:
        print('you won')
    else:
        print('you did not win')

    show_nos_won(my_numbers, win_dict, winning_numbers)


def show_nos_won(my_numbers, win_dict, winning_numbers):
    print('{:<20}'.format('Winning numbers'), end='')
    for number in winning_numbers:
        print('{:>2} '.format(number), end='')

    print()
    print('{:<20}'.format('Your numbers'), end='')
    for number in my_numbers:
        print('{:>2} '.format(number), end='')
    print()

    print('{:<20}'.format(' '), end='')
    for number in my_numbers:
        if win_dict[number]:
            print('{:>2} '.format(CHECK_MARK), end='')
        else:
            print('{:>2} '.format(CROSS), end='')
    print()


def check(winning_numbers, my_numbers):
    """
        returns a dictionary with key as your numbers
        and values as True or False
    """

    return {number: number in winning_numbers for number in my_numbers}


def get_draw():
    return input('Enter draw number #: ')


def get_my_numbers():
    return input('Enter your numbers: ').split(' ')


if __name__ == '__main__':
    main()
