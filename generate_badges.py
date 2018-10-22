#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 python3Packages.requests python3Packages.lxml python3Packages.pypdf2 inkscape
import csv
import pathlib
import subprocess
import tempfile
import time

import requests
from PyPDF2 import PdfFileMerger, PdfFileReader
from lxml import etree


def get_github_avatar(username):
    avatar_dir = pathlib.Path("avatars")
    avatar_dir.mkdir(parents=True, exist_ok=True)
    avatar_path = (avatar_dir / '{}'.format(username))
    if not avatar_path.exists():
        avatar_path.write_bytes(dl_github_avatar(username))
        time.sleep(1)
    return avatar_path


def dl_github_avatar(username):
    r = requests.get("https://api.github.com/users/{}".format(username))
    avatar_url = r.json()['avatar_url']

    r = requests.get(avatar_url, allow_redirects=True)
    return r.content


def process_csv_member(member):
    """
    processes a member coming from a csv entry.
    does nick normalization and avatar fetching,
    returns a dict suitable for members_dict
    :param member:
    :return:
    """

    firstname = member['First Name']
    lastname = member['Surname']
    github = member['GitHub']
    twitter = member['Twitter']
    irc = member['IRC']

    # normalize github and twitter names
    if github.startswith("https://github.com/"):
        github = github[19:]
    elif github.startswith("github.com/"):
        github = github[12:]
    elif github.startswith("'@"):
        github = github[2:]

    if twitter.startswith("https://twitter.com/"):
        twitter = twitter[20:]
    elif twitter.startswith("twitter.com/"):
        twitter = twitter[13:]
    elif twitter.startswith("'@"):
        twitter = twitter[2:]

    nick = github or twitter or irc
    avatar = None

    if github:
        try:
            avatar = get_github_avatar(github)
        except KeyError:
            pass

    return dict(name="{} {}".format(firstname, lastname), avatar=avatar, nick=nick)


def render_svg(member_dicts, output_pdf):
    """
    renders the svg template to pdf using inkscape
    :param output_pdf: where to write the rendered pdf to
    :param member_dicts: list containing (max 10) dicts with name, nick, and avatar elements
    :return: the path to the rendered pdf
    """
    tree = etree.parse("badge-herma-9011.svg")

    # we can't just loop over member_dicts, as that could be != 10 elements,
    # and not replace some placeholders
    for i in range(1, 11):
        if len(member_dicts) >= i:
            member = member_dicts[i-1]
        else:
            member = dict(avatar=None, name='', nick='')

        image_node = tree.find(
            f"//{{http://www.w3.org/2000/svg}}image[@{{http://www.w3.org/1999/xlink}}href='%IMAGE{i}%.png']")

        if member['avatar']:
            image_node.set('{http://www.w3.org/1999/xlink}href', str(member['avatar']))
        else:
            g = image_node.getparent().getparent()
            container = g.getparent()
            container.remove(g)

        flow_paras = tree.findall("//{http://www.w3.org/2000/svg}flowPara")

        # matching by text() seems to be extremely hard,
        # so do it by manually filtering over all flowPara elements
        name_node = list(filter(lambda x: x.text == f"%NAME{i}%", flow_paras))[0]
        name_node.text = member['name']
        nick_node = list(filter(lambda x: x.text == f"%NICK{i}%", flow_paras))[0]
        nick_node.text = member['nick']

    with tempfile.NamedTemporaryFile(suffix='foo.svg') as tf:
        tree.write(tf.name)
        subprocess.check_output(['inkscape', f'--export-pdf={output_pdf}', tf.name])


def main():
    with open("members.csv") as csvfile:
        members = csv.DictReader(csvfile)

        with tempfile.TemporaryDirectory() as td:
            pdf_dir = pathlib.Path(td)
            merger = PdfFileMerger()

            member_dicts = []
            for i, member in enumerate(members):
                if i % 10 == 0:
                    # this also adds an empty badge page, which we want anyhow
                    render_svg(member_dicts, pdf_dir / f'{i}.pdf')
                    merger.append(PdfFileReader(open(pdf_dir / f'{i}.pdf', 'rb')))
                    member_dicts = []
                member_csv = process_csv_member(member)
                member_dicts.append(member_csv)

            merger.write('out.pdf')


if __name__ == "__main__":
    main()
