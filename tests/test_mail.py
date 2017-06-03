#!/bin/env python
# -*- encoding: utf-8 -*-

""" Testing main functionality.

"""

from __future__ import unicode_literals

import io

import todoist_gtd_utils
import todoist_gtd_utils.mail

raw_mail_plain = """Received: from someone (some.ip.address.) with someserver
From: Joakim <joakim.hovlandsvag@gmail.com>
Subject: Short, plain mail
Date: Thu, 25 May 2017 14:11:26 +0200
Message-ID: <eaeaeaeae0010100110@mail.gmail.com>
Content-Type: text/plain; charset="iso-8859-1"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

This is quite a short mail; as we like it!

--
Joakim

"""

raw_mail_latin1 = """Received: from someone (some.ip.address.) with someserver
From: Joakim <joakim.hovlandsvag@gmail.com>
To: =?iso-8859-1?Q?Joakim_Hovlandsv=E5g?= <joakim.hovlandsvag@gmail.com>
Subject: =?iso-8859-1?Q?RE:_S=F8k_is_a_word?=
Date: Thu, 25 May 2017 14:11:26 +0200
Message-ID: <eaeaeaeae0010100110@mail.gmail.com>
Content-Type: text/plain; charset="iso-8859-1"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

This is quite a short mail, with =F8 and =E5, as a test!

--
Joakim

"""

raw_mail_utf8 = """Received: from someone (some.ip.address.) with someserver
From: =?utf-8?Q?Joakim_Hovlandsv=C3=A5g?= <joakim.hovlandsvag@gmail.com>
To: =?iso-8859-1?Q?Joakim_Hovlandsv=E5g?= <joakim.hovlandsvag@gmail.com>
Subject: =?iso-8859-1?Q?RE:_S=F8k_is_a_word?=
Date: Thu, 25 May 2017 14:11:26 +0200
Message-ID: <eee2@mail.gmail.com>
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

New test, with =C3=A6 and =C3=A5!

Even more special: © ▶

--
Joakim

"""

raw_mail_invalid_encoded = """Received: from someone (some.ip.address.) with someserver
From: =?utf-8?Q?Jo=C3=A5kim_Hovlandsv=E5g?= <joakim.hovlandsvag@gmail.com>
To: =?iso-8859-1?Q?Joakim_Hovlandsv=C3=A5g?= <joakim.hovlandsvag@gmail.com>
Subject: =?iso-8859-1?Q?RE:_S=F8k_is_a_word?=
Message-ID: <eee2@mail.gmail.com>
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0

New test, with =C3=A6 and =C3=A5! Or =F8 and =E5

--
Joakim

"""

raw_mail_multipart = """Received: from example.com (2001:1000:500:50::6) ...
From: =?utf-8?Q?Joakim_Hovlandsv=C3=A5g?= <joakim.hovlandsvag@gmail.com>
To: =?iso-8859-1?Q?Joakim_Hovlandsv=E5g?= <joakim.hovlandsvag@gmail.com>
Subject: =?iso-8859-1?Q?RE:_S=F8k_is_a_word?=
Message-ID: <multipart-001@example.com>
Date: Fri, 26 May 2017 09:08:01 +0000
Content-Type: multipart/alternative; charset="UTF-8"; boundary="randomstring"
Content-Transfer-Encoding: 8bit
MIME-Version: 1.0

--randomstring
Content-Type: text/plain; format=flowed; charset="UTF-8"
Content-Transfer-Encoding: 8bit

View this email in your browser
https://example.com/12345.

This is a plaintext title

This is a paragraph where you should've seen a plaintext representation of the
e-mail.

Extra: =C3=A6 and =C3=A5! Special: © ▶

Invalid content: =F8 and =E5!

--
Joakim Hovlandsvag # TODO: Add proper encoded unicode

--randomstring
Content-Type: text/html; charset="UTF-8"
Content-Transfer-Encoding: 8bit

<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<style type="text/css">
. { color: black; background-color: white }
</style>
<title>This is a title</title>
</head>
<body>
<h1>This is an HTML title</h1>

<p>This is a <em>fancy paragraph</em> where you should see a pretty
representation of the e-mail.</p>

<p>Extra content: &aring;, =C3=A6 and =C3=A5! Special: © ▶</p>

<p>Invalid content: =F8 and =E5</p>

<hr>

</body>
</html>

--randomstring--

"""

raw_mail_html = """TODO
"""


def test_simplemail_setup():
    a = io.StringIO('almost empty mail')
    todoist_gtd_utils.mail.SimpleMailParser(a)


def test_empty_mail():
    p = todoist_gtd_utils.mail.SimpleMailParser(io.StringIO(''))
    body = p.get_body()
    assert body == ''
    pres = p.get_presentation(body=False).strip()
    assert pres == ''
    pres = p.get_presentation().strip()
    assert pres == ''


def test_plain_mail():
    p = todoist_gtd_utils.mail.SimpleMailParser(io.StringIO(raw_mail_plain))
    body = p.get_body()
    assert 'short mail' in body
    pres = p.get_presentation(body=False).strip()
    assert len(pres) == 0
    pres = p.get_presentation('_to', '*from')
    print pres
    assert len(pres) > 1
    assert 'Joakim' in pres
    pres = p.get_presentation().strip()
    # TODO: better checks?
    assert len(pres) > 1


def test_latin1_mail():
    p = todoist_gtd_utils.mail.SimpleMailParser(io.StringIO(raw_mail_latin1))
    body = p.get_body()
    assert 'with ø and å, as a test' in body
    pres = p.get_presentation('to')
    print pres
    assert "Joakim Hovlandsvåg" in pres


def test_utf8_mail():
    p = todoist_gtd_utils.mail.SimpleMailParser(io.StringIO(raw_mail_utf8))
    body = p.get_body()
    assert 'æ and å!' in body
    pres = p.get_presentation('from')
    assert "Joakim Hovlandsvåg" in pres
    pres = p.get_presentation('to')
    assert "Joakim Hovlandsvåg" in pres


def test_invalid_encoding():
    """Don't crash if mail is not encoded properly"""
    p = todoist_gtd_utils.mail.SimpleMailParser(io.StringIO(
                    raw_mail_invalid_encoded))
    body = p.get_body()
    assert 'å' in body
    pres = p.get_presentation('from', 'to', body=False)
    assert 'å' in pres


def test_multipart():
    p = todoist_gtd_utils.mail.SimpleMailParser(
            io.StringIO(raw_mail_multipart))
    body = p.get_body()
    print body
    assert 'plaintext title' in body
    assert 'HTML title' in body
    pres = p.get_presentation('from', 'to', body=False)
    print pres
    pres = p.get_presentation('from')
    assert "Joakim Hovlandsvåg" in pres
    pres = p.get_presentation('to')
    assert "Joakim Hovlandsvåg" in pres


def test_decode_quoted_printable():
    tests = (("hei og hopp", "hei og hopp"),
             ("hei =C3=A5 hopp", "hei å hopp"),
             ("hei_=C3=A5_hopp", "hei_å_hopp"),
             )
    for test, answer in tests:
        ret = todoist_gtd_utils.mail.decode_quoted_printable(test)
        assert ret == answer


def test_decode_quoted_printable_latin1():
    tests = (("hei og hopp", "hei og hopp"),
             ("hei =E5 hopp", "hei å hopp"),
             ("hei_=E5_hopp", "hei_å_hopp"),
             )
    for test, answer in tests:
        ret = todoist_gtd_utils.mail.decode_quoted_printable(test, False,
                                                             'latin-1')
        assert ret == answer


def test_decode_quoted_printable_headers():
    tests = (("hei og_hopp", "hei og hopp"),
             ("hei =C3=A5 hopp", "hei å hopp"),
             ("hei_=C3=A5_hopp", "hei å hopp"),
             )
    for test, answer in tests:
        ret = todoist_gtd_utils.mail.decode_quoted_printable(test, True)
        assert ret == answer
