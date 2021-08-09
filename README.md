# Algorytm segmentujący cegiełki 

Algorytm został stworzony z myślą o konkretnym zagadnieniu, jednak może stanowić dobrą podstawę do rozwiązania wielu różnych problemów przestrzennych. Przy korzystaniu z algorytmu należy pamiętać, że ma on charakter bardziej zbliżony do powtarzalnego rozwiązania z zakresu data science niż uniwersalnej biblioteki typowej dla programowania obiektowego. Być może okaże się że aby dostosować go do nowych problemów, danych wejściowych, założeń czy oczekiwań końcowych, będzie należało go zmodyfikować lub uogólnić. W takich przypadkach zachęcamy do dzielenia się swoimi pomysłami oraz zmianami w ramach tego repozytorium.

## Opis

Celem algorytmu jest dokonanie segmentacji poligonów w oparciu o klastrowanie znajdujących się w ich obszarze ważonych danych punktowych.

Algorytm składa się z 3 kolejnych plików przeznaczonych do uruchomienia  (run1.py, run2.py oraz run3.py) oraz biblioteki plików pomocnicznych. Etap 1 i 3 wykorzystuje środowisko GRASS GIS do pre oraz post processingu, natomiast główny etap - drugi - zawiera implementację samego podziału. 

Algorytm dzieli wybrane obiekty poligonowe z wartswy shp na podstawie dopasowania ich id z osobnym plikiem csv. Podział jest wielostopniowy - najpierw może nastąpić cięcie na podstawie arbitralnych linii podziału, następinie w ich obrębie tworzone są regiony, czyli obszary wewnątrz wybranych poligonów których granice odpowiadają linią tnącym. Takimi liniami w naszym przypadku były między innymi granice wodne, wybrane ulice czy linie kolejowe. Przy budowaniu regionów ważnymi czynnikami jest też zapewnienie każdemu regionowi odpowiednią ilość wag punktów (w naszym przypadku były to ważone punkty adresowe) oraz dbanie o komapktowość (wypukłość) kształtu poligonów. 

Następnie każdy z regionów dzielony jest na 1 lub więcej cegiełek końcowych na podstawie łączenia ze sobą poligonów voronoia stworzonych w oparciu o punkty w obrębie regionu. Istotną rolę gra tutaj macierz odległości - budowanie cegiełek odbywa się zgodnie z logiką przyłączania do siebie dobrze skomunikowanych ze sobą punktów.

## Wymagania

- GRASS GIS w wersji przynajmniej 7.8.2 (wspierającej pythona 3)
- Python3 wraz z następującymi bibliotekami: geopandas, topojson, geojson, scipy, requests oraz rtree
- działająca lokalnie lub na serwerze instancja OSRM w oparciu o którą tworzona będzie macierz odległości. 

O OSRM więcej przeczytasz tutaj: http://project-osrm.org/docs/v5.5.1/api/#general-options

## Pliki wejściowe

Algorytm zasilić należy szeregiem starannie przygotowanych danych wejściowych. Nazewnictwo plików czy też kolumn w przypadku warstw shp zmieniać można jako parametry w plikach "run". Są to:

- poligony: posiadające jakąś kolumnę z unikalnymi wartościami
- plik csv z informacją o tym jakie poligony podzielić
- linia tnąca techniczna (a) - jeśli chcemy dokonać bezwzględnego podziału poligonów wzdłuż jakiejś granicy. Nie jest obowiązkowa.
- plik csv z informacją o tym jakie poligony mają być dzielone linią techniczną na dwie części przed podziałem na regiony. Nie jest obowiązkowy
- linie tnące: dowolna ilość plików. Definiowane są w run1.py
- punkty adresowe

## Informacje dodatkowe

W przypadku chęci kontaktu zachęcamy do pisania na maila: info@iqsolution.pl lub mosko@iqsolution.pl
