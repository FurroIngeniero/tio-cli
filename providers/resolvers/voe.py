import re
import json
import base64
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139 Safari/537.36"
    ),
    "Referer": "https://voe.sx/"
}


def rot13(text):

    result = ""

    for c in text:

        if "A" <= c <= "Z":

            c = chr(
                (ord(c) - ord("A") + 13) % 26
                + ord("A")
            )

        elif "a" <= c <= "z":

            c = chr(
                (ord(c) - ord("a") + 13) % 26
                + ord("a")
            )

        result += c

    return result



def clean_separators(data):

    separators = [
        "@$",
        "^^",
        "~@",
        "%?",
        "*~",
        "!!",
        "#&"
    ]

    for sep in separators:

        data = data.replace(
            sep,
            "_"
        )

    return data



def remove_underscore(data):

    return data.replace(
        "_",
        ""
    )



def shift_decode(data):

    return "".join(
        chr(
            ord(c) - 3
        )
        for c in data
    )



def decode_voe(data):

    data = rot13(data)

    data = clean_separators(
        data
    )

    data = remove_underscore(
        data
    )


    data = base64.b64decode(
        data
    ).decode()


    data = shift_decode(
        data
    )


    data = data[::-1]


    data = base64.b64decode(
        data
    ).decode()


    return json.loads(data)



def extract(url):

    print("Abriendo Voe...")


    session = requests.Session()


    response = session.get(
        url,
        headers=HEADERS,
        timeout=15
    )


    response.raise_for_status()


    html = response.text



    # ==========================
    # REDIRECT JAVASCRIPT
    # ==========================

    match = re.search(
        r"window\.location\.href\s*=\s*['\"](.*?)['\"]",
        html
    )


    if match:

        redirect = match.group(1)


        print(
            "Redirect encontrado:"
        )

        print(
            redirect
        )


        response = session.get(
            redirect,
            headers={
                **HEADERS,
                "Referer": url
            },
            timeout=15
        )


        response.raise_for_status()


        html = response.text



    print(
        "URL final:"
    )

    print(
        response.url
    )


    print(
        "Tamaño HTML:",
        len(html)
    )



    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    scripts = soup.find_all(
        "script",
        {
            "type": "application/json"
        }
    )


    print(
        "Scripts JSON encontrados:",
        len(scripts)
    )



    if not scripts:

        print(
            "No hay JSON cifrado"
        )

        return None



    for script in scripts:

        try:

            content = json.loads(
                script.text.strip()
            )


            if not isinstance(content, list):

                continue


            if not content:

                continue



            encrypted = content[0]


            print(
                "JSON cifrado encontrado"
            )


            print(
                "Descifrando Voe..."
            )


            data = decode_voe(
                encrypted
            )


            print(
                "Datos descifrados:"
            )

            print(data)



            # Voe actual usa "source"
            stream = data.get(
                "source"
            )


            if not stream:

                print(
                    "No existe source en los datos"
                )

                return None



            print(
                "\nStream encontrado:"
            )

            print(
                stream
            )


            return stream



        except Exception as e:

            print(
                "Error procesando:",
                e
            )



    print(
        "No se pudo extraer el stream"
    )


    return None