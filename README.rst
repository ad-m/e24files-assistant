.. image:: http://files.jawne.info.pl/static/e24cloud.png
   :target: https://panel.e24cloud.com/referal/GuFfaD31

`e24cloud.com <https://panel.e24cloud.com/referal/GuFfaD31>`_ to polski dostawca usług chmurowych. W swojej ofercie posiada wirtualne serwery, a także przestrzeń ``storage obiektowego`` (coś jak przechowywanie plików). Wszystkie opłaty rozliczane są godzinowo za realne zużycie. 

Storage obiektowe to tani sposób przechowywania dużej ilości plików. Jest to sposób tani, bo przechowywanie 100 GB przez okres miesiąca to tylko 14,40 PLN. Tymczasem konto hostingowe w Hekko o takim rozmiarze to koszt 49,90 PLN. Dodatkowo musisz za nie płacić tyle nawet jak nie zużywasz całości zasobów.

Do przesyłania plików mogą być wykorzystywane 4 protokoły. Najbardziej wiarygodnym i sprawnym jest Swift. Następnie S3. Na końcu FTP i SFTP. Dwa ostatnie są w tej chwili oznaczone jako działające w trybie testowym bez gwarancji poprawności działania. Do obsługi w graficznym interfejsie użytkownika protokołu S3 polecam program `DragonDisk <http://www.s3-client.com/>`_. Do logowania są wykorzystywane klucze API.

W przypadku ``storage obiektowego`` pliki są grupowane są w tzw. bucketach (wiaderkach), które są takimi superkatalogami. Do niedawna dla każdego konta e24cloud przyznawany był jeden zestaw kluczy API, który dawał dostęp do wszystkich danych. Oznaczało to, że gdy będziemy taki klucz zostanie ujawniony zapewni on dostęp do wszystkich danych.

Jednak w ostatnich miesiącach została wprowadzona możliwość tworzenia subkont. Każde subkonto posiada własne klucze API. Oznacza to, że widzi tylko własne buckety, a więc - przykładowo - włamywacz nie ma dostępu do danych innych aplikacji. Wydaje się jednak, że funkcja subkont nie została zaprojektowana z myślą o seperacji aplikacji, a miało to na celu seperację użytkowników. Oznacza to pewne nadmierne komplikowanie rejestracji subkont poprzez np. oczekiwanie numeru telefonu, które oczywiście aplikacje nie posiadają.

W ostatnim miesiącu zostało wprowadzone API do obsługi subkont. Można dzięki temu proces tworzenia subkont i przyznawania im uprawnień znacząco przyspieszyć. Jak również zwiększyć przejrzystość tego procesu analizując jakie dane może oglądać każde z kont.

Końcowo wspomnę, że kliknięcie powyższego loga e24cloud zapewnia podwojenie pierwszej wpłaty.


Instalacja
==========

Kopiowanie kodu źródłowego: 

.. code::
   
   git clone https://github.com/ad-m/e24files-assistant

Instalacja zależności: 

``
sudo apt-get install python-pip && sudo pip install requests pydal python-dateutil
``

Konfiguracja
============

Do poprawnego funkcjonowania aplikacja wymaga utworzenia pliku konfiguracyjnego z danymi kluczy API do panelu administracyjnego e24cloud i kluczy e24files dla głównego konta. Format winien być zgodny z ``config.ini.example``.

Przykłady użycia
================


Zestawienie dostępu do bucketów z poszczególnych kont: 

.. code::

   python report.py --config=config.ini -o output.csv;


Utworzenie subkonta zapewniającego dodatkowego użytkownika bucketu ``test_creator``:

.. code::

   python create_user.py --config=config.ini test_creator --user

Utworzenie bucketu i subkonta mu odpowiadającego:

.. code::

   python create_user.py --config=config.ini test_creator 

Należy zaznaczyć, że aplikacja ``chart_usage.py`` nie wykorzystuje oficjalnego API e24cloud, ani pliku ``config.ini``. Dane dostępowe są pobierane z strony panelu administracyjnego z wykorzystaniem nieudokumentowanego eksportu do JSON. Wobec czego wymagane jest podanie danych do głównego konta użytkownika. Przykładowe wywołanie:

.. code::
   
   python chart_usage.py -u email@example.com -p "BestPassword" -g chart.svg -s 2015-01-01
