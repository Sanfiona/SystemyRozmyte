# System Sterowania Rozmytego dla Pieca do Produkcji Szkła 

Zaawansowany system sterowania oparty na logice rozmytej (Fuzzy Logic), zaprojektowany do stabilizacji temperatury w procesie wytopu szkła. Projekt rozwiązuje problem dużej inercji i opóźnień czasowych występujących w rzeczywistych piecach przemysłowych.

## O projekcie
System realizuje sterowanie temperaturą sklepienia oraz dna pieca szklarskiego. Wykorzystuje zaawansowane modele logiki rozmytej (Mamdani oraz IT2 - Interval Type-2), aby zapewnić wyższą precyzję i efektywność energetyczną w porównaniu do tradycyjnych metod regulacji.

## Technologie i Narzędzia
* **Język programowania:** Python 3.12+
* **Metodyka:** Logika Rozmyta (Typu 1 oraz Typu 2 - IT2)
* **Modelowanie procesów:** Modele FOPDT (First Order Plus Dead Time) dla dynamiki pieca
* **Wizualizacja danych:** Matplotlib / Plotly (wykresy stabilizacji, powierzchnie decyzyjne 3D)

## Kluczowe Funkcje
* **Kaskadowy układ regulacji:** Połączenie klasycznego regulatora PI z rozmytym systemem sterowania IT2.
* **Obsługa niepewności (IT2):** Zastosowanie logiki rozmytej typu drugiego pozwala na lepsze radzenie sobie z zakłóceniami procesowymi niż w standardowych systemach.
* **Analiza zużycia paliwa:** Moduł obliczający efektywność energetyczną w zależności od parametrów sterowania.
* **Symulacja w czasie rzeczywistym:** Silnik symulacyjny wyliczający błędy regulacji oraz czas ustalania temperatury.

## Analiza i Wyniki
Projekt zawiera rozbudowaną sekcję analityczną, w tym:
* **Powierzchnie sterowania 3D:** Wizualizacja bazy reguł i działania silnika wnioskowania.
* **Metryki jakości:** Analiza błędów regulacji i porównanie wydajności różnych modeli sterowników.
* **Wykresy trendów:** Prezentacja stabilizacji temperatury w czasie.

## Autorzy
Projekt został zrealizowany przez zespół w składzie:
* Milena Pasterczyk
* Karol Ogonowski
* Piotr Pająk
* Dawid Sudol

*Projekt przygotowany w ramach studiów informatycznych na Uniwersytecie Rzeszowskim.*

---
*Informacja: Przy optymalizacji kodu oraz strukturze dokumentacji wykorzystano narzędzia AI w celu zapewnienia najwyższej jakości technicznej.*

