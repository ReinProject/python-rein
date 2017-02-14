kā sagatavot Rein, lai sāktu pelnīt bitcoinus

Ievads/INTRODUCTION

Rein ir jauns centralizēts darba tirgus kas piedāvā drošu un vieglu veidu kā pelnīt bitcoinus un iespējas no profesionāļiem.Visu vieglāku padara digitālo parakstu līgumi un iespēja dabūt to ko vēlies.Uz doto brīdi Rein joprojām ir Aplha versijā, šim procesam ir nepieciešams command line client.Kaut gan šo programmu ir ļoti viegli ieinstalēt ar komandām kuras tu pats sapratīsi uzreiz pēc to darbības.

Šajā pamācībā mēs jums parādīsim kā izmantot Rein un pelnīt bitcoinus.Mēs jums arī parādīsim kā ģenerēt dažus no standalone Bitcoin atslēgām kas būs vajadzīgas priekš jūsu Rein profila. 




Izpildes laiks/TIME TO COMPLETE
10-20 minūtes




Priekšnosacījumi/PREREQUISITES

Lai sāktu šo pamācību, jums būs nepieciešamas dažas lietas.
Jums ir vajadzīgs Python 1.7 ar pip ieinstalētu jūsu datorā, un jāpārbauda vai datorā nav vīrusu.

Jums arī ir vajadzīgs Bitcoin Core (vai kaut kas līdzīgs). Tas nav domāts lai viss tiktu sinhronizēts uz blockchain.Mēs to izmantosim lai ģenerētu adreses(BTC) , bet lai varētu saņemt samaksu un to tērēt jums vajadzētu visu sinhronizēt vēlāk.

Jums ir vajadzīgs veids lai būtotos iekš GNU+Linux Live CD environment. Iespējams izmantojot unetbootin un pēdējās versijas Ubuntu ISO ar thumb drive.

Jums būtu vajadzīgas dažas flešatmiņas kur turēt bitcoin wallet kopiju.

Kad visi priekšnosacījumi ir izpildīti, sāksim instalēt python-rein client un palīdzības aplikācijas



1.Solis -- Instalēt python=rein un palīdzības aplikācijas

Pirmais solis izmantotojot Rein lai pelnītu bitcoinus ir, ieintstalēt python-rein aplikāciju jūsu datorā. Šobrīd vislabākais veids to instalēt ir , kopējot to no Github krātuves. Protams nākotnē tas visticamāk būs iespējams no package manager.

Kopēšana

Kopēsim python-rein jūsu mapē ar šo komandu:
$ git clone https://github.com/ReinProject/python-rein.git ~/python-rein

Jums tagad vajadzētu būt python-rein kopijai krātuvē iekš ~/python-rein

Instalēt klientu

Pirms instalēšanas nomaini python-rein atrašanās vietu:
$ cd python-rein

Nu mēs varam to instalēt ar šo komandu:
$ sudo pip install --editable .

Ar ieinstalētu Rein, mēs varam pārbaudīt vai viss izdarīts parezi - palaižot to.
$ rein

Šim vajadzētu parādīt palīdzības lapu ar daudzām komandām.

Tu vari izmantot --help ar jebkuru komandu lai iegūtu vairāk informācijas; piemēram:
$ rein setup --help

Lejupielādēt palīdzības aplikācijas

Lai palīdzētu tev izveidot digitālo parakstu izmanto bitcoin-signature-tool un modificētu versiju no Coinbin, kas veidots tieši priekš Rein.
$ cd 
$ mkdir Rein && cd Rein
$ git clone https://github.com/ReinProject/bitcoin-signature-tool.git
$ git clone https://github.com/ReinProject/coinbin.git

Jums tagad vajadzētu būt bitcoin-signature-tool un Coinbin  lai spētu izveidot parakstus un Bitcoin ECDSA private keys(Privātās atslēgas).

Zīme: Ja jūs jau zinat visu par Bitcoin adresēm, parakstiem un makiem jūs varat automātiski doties uz 3.soli.





2. Solis -- Sagatavo Bitcoin maku

Rein atļauj izveidot cik vien identitātes vēlies, bet visur kur uzticība un reputācija ir svarīga tu drošvien vēlēsies izmantot vienu identitāti. Šīs identitātes ir definētas no Bitcoin ECDSA keypair, ko mēs saucam par identitātes galvano adresi.

Šeit mēs jums parādīsim , kā izmantot Bitcoin Core (vai kaut ko līdzīgu), lai ģenerētu Bitcoin adreses un saglabāt private keys, lai izmantou vēlāk.



Izveido Bitcoin maku

Bitcoin Core piedāvā ļoti vieglu veidu kā izveidot Bitcoin adreses. kad programma bitcoin-qt ir atvērta pirmo reizi, tā ģenerē maku automātiski.šis maks var būt šifrēts lai aizsargātu to no citām maka kopijām.

Pirms izveidojam adresi, šifrēsim maku.

Izmanto stipru paroli ar vismaz 10 zīmēm. Ir ļoti svarīgi, ka tev ir šī parole, jo tā būs jāizmanto nākotnē, tāpēc ielieciet to password manager, pierakstiet kaut kur, vai iegaumējiet. Ja jūs pazaudējat paroli vai maka failu, jūs zaudēsiet pieeju savai Rein identitātei un Bitcoiniem.


Dublē maku

Izveido dažas kopijas makam, ielieciet to flešatmiņās vai jebkur citur, kur var uzglabāt atmiņu. Ideāli būtu ja jūs kopijas saglabātu seifā vai citā ļoti drošā vietā.






3.Solis -- Izveido lietotāja profilu

Izveidosim jūsu Rein lietotāja profilu, saukts arī par identitāti.
$ rein start

Jums vajadzētu redzēt tīkla formu ko aizpildīt. Atceries to, ka visa informācija būs arī skatāma citiem lietotājiem atskaitot privātās atslēgas un paroles.

Dabū adresi np Bitcoin-Qt

Dabūsim galvano Bitcoin adresi no Bitcoin-Qt. Dodaties uz failu -> Receiving Addresses... Un spied NEW . Nokopē pirmo adresi un ielīmē to šeit.

Nākamais, mēs dabūsim citu adresi no Bitcoin-Qt and iekopēsim to Delegate Bitcoin address



Dabū private key no Bitcoin-Qt

Mums vajadzēs private keys priekš abām divām adresēm. Vispirms dabūsim private key priekš Delegate address.

Atver Debug Window to the Console tab.

Ieraksti doto komandu :
dumpprivkey <your address>

Pēc tam izprintēsies private key.

Iekopē šo private key iekš Delegate Bitcoin private key lauciņā.

Izvēlies vai būt starpniekam vai arī nē, izvēlies savu samaksu. Piemēram, ja liksi 3% tu dabūsi 0.003 BTC par 0.1 BTC pārskaitīšanu vai nu vajadzēs atrisināt strīdu vai arī nē. Spied next.




Paraksti dokumentu.

Balstoties uz informāciju ko izveidoji, tiks izveidots dokuments. Lai pabeigtu profila veidošanu, mēs parakstīsim šo tekstu izmantojot Bitcoin Signature Tool.

Atver savu pārlūku un atver ~/Rein/bitcoin-signature-tool/index.html. Spied Sign un atkārto procedūru lai dabūtu private key priekš Master Bitcoin Adreses(Galvenās).

Private key būs iekš private key lauciņā sarkanā krāsā.

Atver enrollment,txt ar jebkuru teksta editoru, izgriez saturu un ielīmē iekš Message box dzeltenā krāsā.

Spied "Sign Message" lai ģenerētu parakstu. Teksta bloks kas satur vēstuli un parakstu būs ģenerētu zaļajā lauciņā. Uzspied uz to un nokopē tekstu.

Iekopē tekstu savā teksta editorā un saglabā failu.

Tad kad tas ir pabeigts, tu būsi beidzis veidot profilu , nospiežot enter.

Python-rein pārbaudīs parakstu teksta failā un ja tas būs derīgs, visu dokumentu saglabās lokālajā datubāzē.

Nu mēs esam gatavi nākamajam solim, kas ir reģistrēties Rein serveros.






4.Solis -- Enable Tor

Privātums ir svarīga lieta ko Rein arī piedāvā saviem lietotājiem.Tor Browser Bundle lietotājiem, viena komanda var ieslēgt, lai viss ietu caur Tor.
rein tor true




5.Solis -- Reģistrē un Augšupielādē Dokumentu

Rein izmanto microhosting serverus lai kopīgotu datus starp lietotājiem. Savienosim python-rein ar diviem serverim, kuri darbojas kā community service priekš ReinProject.org.
$ rein request rein1-sfo.reinproject.org:2016

Tev vajadzētu parādīties ziņai kas saka , ka tev ir 1 bucket augšējā serverī. Atkarto to ar otru serveri.
$ rein request rein2-ams.reinproject.org:2016

Atkal vajadzētu parādīties ziņai kas saka,ka tev ir 1 bucket augšējā serverī.



Augšupielādē dokumentu.

Nākamais, mēs sinhronizēsim lokālo Rein datubāzi, kura satur tikai vienu dokumentu, ar serveriem kuriem pieslēdzāmies pirms tam.
$ rein sync

Sī komanda pārbauda katru reģistrēto serveri priekš dokumentiem ko izveidojām lokāli un augšupielādes kuras ir nepareizas vai vēl neeksistē.Šajā gadījumā, divi serveri tiks pārbaudīti un nevienā nebūs tavs dokuments, parādīsies divas jaunas augšupielādes.

Nu tu esi gatavs sākt pelnīt bitcoinus ar Rein.

Lai pārbaudītu statusu savam profilam un pārskaitījumus kuros esi iesaist;its, palaid Rein status.

Ja esi starpnieks kurš atrisina strīdu, tu redzēsi pārskaitījumu sarakstā iekš output.Darbinieki un darba devēji noteikti ar tevi sazināsies iekš Contact sekcijas tavā dokumentā.

Ja kaut ko vēlies sīkāk paskaidrotu, augšā ir video Rein - Getting started: Install and Setup - part 2/4

Ja ir kādi jautājumi, korekcijas vai rekomendācijas lūdzu dalies ar kļudu šeit vai iesniedz pull request.