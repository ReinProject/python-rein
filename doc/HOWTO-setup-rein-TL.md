#Paano i-setup ang Rein Para Magsimula kumita ng Bitcoin 

##Pagpapakilala ng Rein

Ang Rein ay bagong desentrelisadong labor market na nagbibigay na ligtas at ng madaling paraan para kumita ng Bitcoin at para makakuha ng serbisyo mula sa mga professionals saan man sa mundo. Ito ay pinasimple ang proseso sa pagpasok sa digitaly-signed contracts at kumilos ng totoo para makuha nila ang kanilang gusto.Sa ngayon , ang Rein ay nasa alpha pa rin, ang proseso na kailangan na gamitin ang command line. Gayunman , ang software ay madaling iinstall kasama ang commands na  magkakaroon ng kahulugan sa sandaling makita mo ito sa aksyon.

Sa tutorial na ito,  ipapakita namin kung paano gamitin ang Rein para kumita ng Bitcoin o paano matapos ang trabaho online. Ipapakita rin namin kung paano mag-generate ng pareha ng standalone Bitcoin keys na bubuo ng mga batayan para sa iyong user account sa Rein. 

## Oras ng pagkumpleto

10-20 minutos

##Mga Kailangan


Bago sundan ang tutorial , kailangan mo muna ang mga bagay na ito.

Kailangan meron kang Python 2.7 na may pip na installed sa iyong computer at kailangan tiyakin na walang malware ang computer mo.

Kailangan meron kang ding  Bitcoin Core (o katulad) na installed. Hindi na kailangan na sync'd sa blockchain para dito sa HOWTO. Gagamitin natin ito upang mag-generate ng addresses dahil para ma tiktikan natin ang payments at sa paggastos ng kinita , gugustuhin mo ding sync it up mamaya.

Kailagan may paraan ka din para i-boot ito sa GNU+Linux Live CD environment. Marahil sa paggamit ng unetbootin at ang pinaka bagong Ubuntu ISO na may thumb drive.

Kailagan mo ding ng mga flash drives na kung saan i-baback up ang Bitcoin wallet.

Kung lahat ng kailagan ay nagawa muna, lumipat tayo sa pag  installing ng python-rein client at helper apps.

##Unang hakbang -- Iinstall ang python-rein at helper apps

Ang unang hakbang sa paggamit ng Rein para kumita ng Bitcoin ay iinstall ang python-rein software sa inyong computer.Sa ngayon , ang pinakamabisang paraan sa pag install ng python-rein ay ang pag clone nito sa Github repository. Sa hinaharap, puwede na ito sa iyong package manager.

###I-clone ang repo    

Ating i-clone ang `python-rein` sa inyong home folder gamit ang command na ito:

    $ git clone https://github.com/ReinProject/python-rein.git ~/python-rein

Kailangan may kopya ka na ng `python-rein` repository sa ~/python-rein

###Install ang client

Bago ang iinstall, ibahin mo muna ang `python-rein` directory:

    $ cd python-rein

Ngayon ma-iinstall na natin gamit ang command na ito:

    $ sudo pip install --editable .

Kapag na installed na ang rein, masusuri na natin ng madalian kung tama ang pag set up natin dito sa pamamagitan ng pa run nito.

    $ rein
    
Ito ay dapat magpakita ng isang pahina ng help na kung saan nakasulat ang maraming commands.

Puwede mong gamitin ang --help kasama ng kahit anong commands para makakuha ng madaming impormasiyon; halimbawa:

    $ rein setup --help

###I-download ang helper apps

Para matulungan ka gumawa ng digital signatures ang bitcoin-signature-tool at ang modified version ng Coinbin na built na sa Rein.

    $ cd 
    $ mkdir Rein && cd Rein
    $ git clone https://github.com/ReinProject/bitcoin-signature-tool.git
    $ git clone https://github.com/ReinProject/coinbin.git

Kailagan meron ka na ng bitcoin-signature-tool at Coinbin para sa Rein para matulungan ka gumawa ng ng signatures kasama Bitcoin ECDSA private keys.

Paalala: Kung familiar ka na sa  Bitcoin addresses, signatures at wallets, puwede mo na iskip at dumeretso na sa ikatlong hakbang ang pag setup ng iyong Rein identity.

##Ikalawang hakbang -- Maghanda ng Bitcoin Wallet

Ang Rein ay mag bibigay ng abilidad para magkaroon ng maraming katauhan kung gugustuhin mo, kahit na sa anong bagay ang tiwala at repustasiyon ang mahalaga, kailangan mo maki transact sa iyong main identity.Itong identities na ito ay tinutukoy sa pamamagitan ng Bitcoin ECDSA keypair (i.e. ang address) na tinatawag namin na master address.

Sa setup na ito,  ipapakita namin kung paano gamitin ang **Bitcoin Core (o mga katulad)** para maka generate Bitcoin ng addresses at isave ang private key para mas madaling gamitin mamaya.

###Gumawa ng encrypted Bitcoin Wallet

Ang Bitcoin Core ( mga katulad)  ay mag bibigay ng mas simpleng paraan para gumawa ng Bitcoin addresses. Kapag ang program `bitcoin-qt`ay kakabukas na unang beses, itoy awtomatikong mag generate ng wallet . Itong wallet na ito ay puwedeng maging encrypted paea ma protektahan laban sa  theft at kopya ng wallet  na puwedeng ibacked up sa removable media.
	
Bago tayo makatanggap ng kahit  anonb addresses, Ating i-encrypt ang wallet.

<img src="http://reinproject.org/img/encrypt.png">

Mag Enter ng strong password na at least 10 characters. Ito ay **napakaimportante** ang iyong password para sa sandaling kailangan i-access sa hinaharap dapat itago ito sa iyong password manager, isulat ito , at/o kaya isaulo ito. Kapag nawala mo ang iyong password o kaya ang wallet file,mawawala na rin ang access mo sa iyong Rein identities at sa Bitcoin funds kung saan nakalagay ang keys.

###I-backup ang Wallet

Gumawa ng ilang backup copies ng iyong wallet sa removable media katulad ng flash drives, memory cards, o kaya optical media. At kailangan ding itago ito sa safe o sa safe box deposit.

<img src="http://reinproject.org/img/backup.png">

##Step 3 -- Gumawa ng User Account

Tayo'y gumawa ng iyong Rein user account, na mas kilala sa software bilang identity.

    $ rein start
    
Kailagan makakita ng web form para sa pag fill out. Paalala na ang iyong impprmasyon sa iyong set up maliban sa privare keys ay magiging bukas sa publiko at magiging makita ng mga user kapag na pushed na ito server. 

###Kumuha ng address galing sa Bitcoin-Qt

Tayo'y kumuha ng  Master Bitcoin address galing sa Bitcoin-Qt. Dito kailangan mo pumunta sa  File -> Receiving Addresses... at i-click hanggang lumabas ang bagong pares ng address.Kopyahin at i-paste dito.

Susunod, kukuha tayo ng ibang  address sa Bitcoin-Qt at kopyahin at i-paste ito sa Delegate Bitcoin address.

<img src="http://reinproject.org/img/rein-web-enroll.png">

###Kumuha ng private key sa Bitcoin-Qt

Kailangan natin ng private keys para sa dalawang addresses sa itaas. Simulan natin sa pagkuha ng the private key sa Bitcoin-Qt para sa Delegate address.

Buksan ang  Debug Window na nasa Console tab.

<img src="http://reinproject.org/img/debug.png">

At diyan itype natin ang sumusunod na command:

    dumpprivkey <your address>

<img src="http://reinproject.org/img/dumpprivkey1.png">

Pagkatapos ng pangalawa , ito ay magpiprint out ng private key.

<img src="http://reinproject.org/img/dumpprivkey2.png">

Kopyahin ang key sa Delegate Bitcoin private key field.

Mamili kung gusto mo maging mediator o kaya hindi at mag set ng fee. Halimbawa , kapag naglagay ka ng 3% dito, puwede kang kumita ng 0.003 BTC sa pag mediating ng 0.1 BTC transaction, kung kailangan mo man mag resolve ng dispute o hindi. Click next.

###I-sign ang enrollment

Base sa impormasyong na iyong inilagay sa document o tinatawag na enrollment itoy magagawa. Para matapos ang paggawa ng iyong user account, aming i-sign itong text gamit ang Bitcoin Signature Tool.

Buksan ang iyong browser at buksan ang  file sa ~/Rein/bitcoin-signature-tool/index.html. I-Click sa ibabaw ng Sign tab at ulitin ang nasa itaas na paraan para makakuha ng private key para sa iyong Master Bitcoin address.

<img src="http://reinproject.org/img/master-signing.png">

Ang private key ay mapupunta sa Private Key box na shaded ng red.

Buksan ang enrollment.txt sa iyong paboritong plain-text editor, i-cut ang content  i-paste ito sa  Message box na shaded sa yellow.

Click "Sign Message" para mag generate ng signature. Ang block ng text na kasama ang message at signature ay mag generate sa green area. I-Click para ma highlight ito at kopuyahin ang text.

I-Paste iyang text sa editor at i-save ang file.

Kapag itoy tapos na, ikaw ay makokompleto na ang iyong account setup sa pamamagitan ng pagpindot sa enter back in the terminal window kung saan ang `rein setup` ay nag run.

Ang Python-rein ay susuriin ang  signature na nasa text file na ginawa mo at kung ito ay valid, itoy i-save sa  entire signed document sa kanilang local database. 

Ngayon ay handa na tayo sa susunod na hakbang,  kung saan nag register sa Rein servers.

##Ikaapat na hakbang -- Paganahin ang Tor (optional)

Ang privacy ay napakahalagang features na pakay ibigay ng Rein sa users. Para sa users ng [Tor Browser Bundle](https://www.torproject.org), isang command na pwedeng i-run at paganahin ang lahat ng traffic ay idudugtong sa pamamagitan ng Tor.

    rein tor true

##Step 5 -- Mag Register at I-upload ang Enrollment

Ang Rein ay gumagamit ng microhosting servers para magbigay ng data sa mga users. Ikonekta ang python-rein sa dalawang servers, na kung saan nag  operated bilang community service ng ReinProject.org.

    $ rein request rein1-sfo.reinproject.org:2016
    
Ngayon merong mensahe na nagsasabi na you have a 1 bucket at the above server.Ulitin sa  pangalawang server.

    $ rein request rein2-ams.reinproject.org:2016

Muli , ang mensahe ay magpapakita at kinukumpirma na meron kang 1 bucket at the above server.

### I-Upload ang Enrollment

Susunod, ating isync sa iyong local Rein database na kung saang nakapaloob ang isang document lamang , sa servers ating i `request`-ed sa dating section .

    $ rein sync

Itong command ay susuruin isat isa ang registered server para sa documents na ating ginawa locally at i-uploads ang mga mali o ang hindi pa lumalabas. Sa kasong ito, ang dalawang server ay susuriin at kahit meron ang aming documents, kaya ang dalawa uploads ay mangyayari.

Ngayon ay puwede ka ng kumita ng Bitcoin gamit ang Rein.

Sa pagsusuri ng  status na iyong account at ano mang transaksyon na ikaw ay kasali , run `rein status`.

Kapag ikaw ay isang mediator kailangan mo solusyunan ang dispute, makikita mo ang transaksyon na nakalista sa output. Ang Workers at ang  job creators kailangan ding payuhan ka sa pamamagitan ng impormasyon sa Contact section na iyong enrollment.

Para sa iba pang detalye , na nakasaad sa itaas ay makikita sa video [Rein - Simulan: Install at Setup - part 2/4] (https://www.youtube.com/watch?v=PaF5URG2dLc)

Para sa iba pang impormasyon, pagtatama, o rekomendasyon kami nakikiusap na ipost ang issue dito o mag sumite ng pull request.
