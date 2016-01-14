PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE identity (
	id INTEGER NOT NULL, 
	name VARCHAR(250) NOT NULL, 
	contact VARCHAR(250) NOT NULL, 
	maddr VARCHAR(64) NOT NULL, 
	daddr VARCHAR(64) NOT NULL, 
	dkey VARCHAR(64) NOT NULL, 
	will_mediate BOOLEAN NOT NULL, 
	mediation_fee FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (will_mediate IN (0, 1))
);
INSERT INTO "identity" VALUES(1,'Bob','bob@example.com','1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN','1CptxARjqcfkVwGFSjR82zmPT8YtRMubub','KzugCvcGHbDDQREj6jKmLfJebUfHjYUaRafEwLJW4he6Ns2YomGV',0,1.0);
INSERT INTO "identity" VALUES(2,'Alice','alice@example.com','1Djp4Siv5iLJUgXq5peWCDcHVWV1Mv3opc','19skaV7ZDvSe2zKXB32fcay2NzajJcRG8B','L3r5FyiLtSyxdviznVbLXD2S92dFhx3ACY8qrq17cPCbMembs1J1',1,1.0);
INSERT INTO "identity" VALUES(3,'Charlie','charlie@example.com','1M6DBU6LoaskwWxfpqaaZ1Z85nsixM97Tc','18UZN58o4fnJpfC7nMBQ5iapoLmqfPf3m5','Kxi82sDJUyAsV6nzujzS2k6pmryDvH7xLCmTRt8jvfzY5fYN6P8c',0,1.0);
CREATE TABLE bucket (
	id INTEGER NOT NULL, 
	identity INTEGER NOT NULL, 
	remote_id VARCHAR(250), 
	date_created DATETIME, 
	url VARCHAR(250) NOT NULL, 
	bytes_free INTEGER, 
	expires DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO "bucket" VALUES(1,1,'1','2016-01-14 02:31:24.000000','http://localhost:5000/',1048576,NULL);
INSERT INTO "bucket" VALUES(2,2,'2','2016-01-14 02:37:16.000000','http://localhost:5000/',1048576,NULL);
INSERT INTO "bucket" VALUES(3,3,'3','2016-01-14 02:39:12.000000','http://localhost:5000/',1048576,NULL);
CREATE TABLE document (
	id INTEGER NOT NULL, 
	identity INTEGER NOT NULL, 
	doc_type VARCHAR(64), 
	doc_hash VARCHAR(250) NOT NULL, 
	contents VARCHAR(8192) NOT NULL, 
	source_url VARCHAR(250) NOT NULL, 
	source_key VARCHAR(64), 
	sig_verified INTEGER, 
	PRIMARY KEY (id)
);
INSERT INTO "document" VALUES(1,1,'enrollment','d9e6f5e335dd6e2efd33cdd548fa732041e2706fa23574600970acce6cb839e0','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein User Enrollment
User: Bob
Contact: bob@example.com
Master signing address: 1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN
Delegate signing address: 1CptxARjqcfkVwGFSjR82zmPT8YtRMubub
Willing to mediate: False
-----BEGIN SIGNATURE-----
1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN
G+I+yr15oWQJUlxC+FO5Bw8Oc1ExfGNPH0Bn0zBOSmjpZ+c/a8gvdabEaPLEdOI101lHLDmM42s94GUuUAUTFD0=
-----END BITCOIN SIGNED MESSAGE-----
','local',NULL,1);
INSERT INTO "document" VALUES(2,2,'enrollment','fa674c44af1840288f38f43497610434f92a35883551f7712aa6d2e53beaa4f3','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein User Enrollment
User: Alice
Contact: alice@example.com
Master signing address: 1Djp4Siv5iLJUgXq5peWCDcHVWV1Mv3opc
Delegate signing address: 19skaV7ZDvSe2zKXB32fcay2NzajJcRG8B
Willing to mediate: True
Mediator pubkey: 029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005
Mediation fee: 1.0%
-----BEGIN SIGNATURE-----
1Djp4Siv5iLJUgXq5peWCDcHVWV1Mv3opc
H2ynZXU3ZBfeJQsRasA8/RRLjdpRYnMVtz5YBU0Ztos8+eOyWZ1DuW8J8ydVen+Pp8bbk0K/kxK0NOy55veKDJw=
-----END BITCOIN SIGNED MESSAGE-----
','local',NULL,1);
INSERT INTO "document" VALUES(3,3,'enrollment','5d91b8b1b11060e19e2dc82880a814c9687369f4dcfee3f995bc291d3b42538c','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein User Enrollment
User: Charlie
Contact: charlie@example.com
Master signing address: 1M6DBU6LoaskwWxfpqaaZ1Z85nsixM97Tc
Delegate signing address: 18UZN58o4fnJpfC7nMBQ5iapoLmqfPf3m5
Willing to mediate: False
-----BEGIN SIGNATURE-----
1M6DBU6LoaskwWxfpqaaZ1Z85nsixM97Tc
H2RKR84OHoAJcg0MogALwXR8MLo9zRvMNmRQr0t7MPhrg5Gx2pUYpGUx1hC4W60ljn40ghhEzQ/kDHH+z/lZPrM=
-----END BITCOIN SIGNED MESSAGE-----
','local',NULL,1);
INSERT INTO "document" VALUES(4,1,'job_posting','1d4792e8d9290f1d45436c4346a8a53b85c339e3427bc5aaa9971a161c7d5a87','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein Job
Job creator''s name: Bob
Job creator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Mediator''s name: Alice
Mediator''s public key: 029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005
Job name: A Software Widget
Category: Software
Description: I need a widget for my website. It needs to be done in Javascript and must show a message to each visitor, basically "Hello World!" is the message. In any case, the site is http://example.com so please check it out before bidding. Thanks!
Job ID: fyzfrxtrttcv8o04oj53
-----BEGIN SIGNATURE-----
1CptxARjqcfkVwGFSjR82zmPT8YtRMubub
H3qtO/IOayLkuRdUX/ElBXQVh/yIddcWq6XmfwpHvwajPhTmsHmJTgqRczMNGNRyU5UsM5N5qJB5rI8wK4aD+/0=
-----END BITCOIN SIGNED MESSAGE-----','local',NULL,1);
INSERT INTO "document" VALUES(5,1,'job_posting','a58c4058fbaf69aaaec30c6cc9fd737bd4f336e8b0cf542c7505096f4ae194a9','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein Job
Job creator''s name: Bob
Job creator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Mediator''s name: Alice
Mediator''s public key: 029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005
Job name: Winter Picnic Flyer
Category: Graphics
Description: My neighborhood is having its yearly Winter picnic. We live in a very mild climate. I need a flyer as a PDF that says in no uncertain terms that  there will be a picnic, it will happen at <date> at <time> and that <entertaining emotion> will be had! Thanks!
Job ID: 6g0j1m22lec5btt8b9t7
-----BEGIN SIGNATURE-----
1CptxARjqcfkVwGFSjR82zmPT8YtRMubub
IGWk0/xKwB6+TKGOOx0DATxJm/9PdlQN4H4Z2gfAbrbVMGnhnSwRY4J0hoZCsnmh6WM6mkbhU3fnGP3YuZEBCEs=
-----END BITCOIN SIGNED MESSAGE-----','local',NULL,1);
INSERT INTO "document" VALUES(6,3,'bid','cbb286eac8af2304f91e9504a5f73cb8c96250a18e4ae57eac0e86dc4eae71f0','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein Bid
Worker''s name: Charlie
Worker''s public key: 02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519
Job ID: fyzfrxtrttcv8o04oj53
Job creator''s name: Bob
Job creator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Description: Hi Bob, I can get this done for you no problem. I am a Javascript whiz and have done "Hello World!"-type jobs many times. I can have this done for you within 3 days of your offer. Thank you, sir.
Bid amount (BTC): 0.05
-----BEGIN SIGNATURE-----
18UZN58o4fnJpfC7nMBQ5iapoLmqfPf3m5
H1+txkpc6vXvncLrELwVVowfr64cwoOsV/pTQ+mNTiMuCYBFdCr1pAIyv/L5rFbpNDRC019aVxS6UVl6kRF4umE=
-----END BITCOIN SIGNED MESSAGE-----','local',NULL,1);
INSERT INTO "document" VALUES(7,3,'bid','db0d86febbddd5dd5e2dcf6c654d4a346b659a00e783a4b6539468bcd2b7d77b','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein Bid
Worker''s name: Charlie
Worker''s public key: 02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519
Job ID: 6g0j1m22lec5btt8b9t7
Job creator''s name: Bob
Job creator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Description: In addition to my Javascript creds, I''m quite handy with Acme Photojobber and can create a few designs for you to choose from. TI will also include two rounds of revisions on your selected design for the bid amount. I can get this entire job done for you within 7 days. Thank you, sire.
Bid amount (BTC): 0.1
-----BEGIN SIGNATURE-----
18UZN58o4fnJpfC7nMBQ5iapoLmqfPf3m5
H34HeYI+xo+mQR5n97ZAtHWoDZkfSNMuRp3144SBF0ZYRN3TyJrrdHief4/3vXY1nxrsmS7GVKQyTLI3uBveC7c=
-----END BITCOIN SIGNED MESSAGE-----','local',NULL,1);
INSERT INTO "document" VALUES(8,1,'offer','f4ccd04cb736d05b9470150e591e8bad321428fb89f3de490c9fec301dc76fb9','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein Offer
Job creator''s name: Bob
Job creator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Worker''s name: Charlie
Worker''s public key: 02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519
Mediator''s name: Bob
Mediator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Mediator escrow address: 3R1Pzho6Yca27AceUHBYnmg6S2NbT1LtLs
Mediator escrow redeem script: 21029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005ad5221026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc2102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651952ae
Primary escrow address: 3GJrubCa1wCFMUqnwPhuyeQXdWTD8hecdG
Primary escrow redeem script: 522102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651921026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc21029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb00553ae
Description: I''m not sure what to write here but getting it done in a few days sounds good. Let us begin!
Bid amount (BTC): 0.05
Job ID: fyzfrxtrttcv8o04oj53
-----BEGIN SIGNATURE-----
1CptxARjqcfkVwGFSjR82zmPT8YtRMubub
IHBppS2AkGAnXYbjOx+Y5m9IFrdohq7NizcOzqVkapnvaY7nmuO3lFwbnV9AFWwTj5/QFTge3Jww8sT3f/kl3+o=
-----END BITCOIN SIGNED MESSAGE-----','local',NULL,1);
INSERT INTO "document" VALUES(9,1,'offer','9c213c02ee746f40298e4585b9652db28ef2d203ee054ef31b9954fe8d998052','-----BEGIN BITCOIN SIGNED MESSAGE-----
Rein Offer
Job creator''s name: Bob
Job creator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Worker''s name: Charlie
Worker''s public key: 02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519
Mediator''s name: Bob
Mediator''s public key: 026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc
Mediator escrow address: 3Di3fKuqVLoVirvxJ7gRHvbE5hxEFWViUU
Mediator escrow redeem script: 21029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005ad522102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651921026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc52ae
Primary escrow address: 3A3ghdXaaKCcMUTfL2XXMLJhnUZUimYF2n
Primary escrow redeem script: 5221029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb0052102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651921026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc53ae
Description: You do flyer''s too? Yes, please!
Bid amount (BTC): 0.1
Job ID: 6g0j1m22lec5btt8b9t7
-----BEGIN SIGNATURE-----
1CptxARjqcfkVwGFSjR82zmPT8YtRMubub
IP4pFlJpPEyXHRtHnvm7UPNpF1VE0Puzfi+nuYorqEo2ZT+u87e0QXwNyNJC7SrlshO1iB59XEDjCQiSL4uGjxI=
-----END BITCOIN SIGNED MESSAGE-----','local',NULL,1);
CREATE TABLE placement (
	id INTEGER NOT NULL, 
	doc_id INTEGER NOT NULL, 
	url VARCHAR(250) NOT NULL, 
	remote_key VARCHAR(64) NOT NULL, 
	verified INTEGER NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO "placement" VALUES(1,1,'http://localhost:5000/','IEU36G2PGDCHT1X1BEDWYWZI0HBX7VY2',1);
INSERT INTO "placement" VALUES(2,2,'http://localhost:5000/','WC9L4DBYGBWNSKBY1WKSZIR3AIQP3ABG',1);
INSERT INTO "placement" VALUES(3,3,'http://localhost:5000/','BQXDTTFMMVBH4AHCV1KUPEQM7S4QM2PE',1);
INSERT INTO "placement" VALUES(4,4,'http://localhost:5000/','0AMBJAFQY4I6BBVPJ72S7BR2ZBU2WZLS',1);
INSERT INTO "placement" VALUES(5,5,'http://localhost:5000/','LVE66MN83IKATVC61SAG0IARNZGSOIGQ',1);
INSERT INTO "placement" VALUES(6,6,'http://localhost:5000/','5VIEIBKLVC69XD6JTY9PSMKX49Q95FWV',1);
INSERT INTO "placement" VALUES(7,7,'http://localhost:5000/','MZTNIL22VFZV07HH7K717GJ7R69VPK6S',1);
INSERT INTO "placement" VALUES(8,8,'http://localhost:5000/','WFH5RH2L6CFAQQMHHTEFJ0WAQOZWOXWJ',1);
INSERT INTO "placement" VALUES(9,9,'http://localhost:5000/','FX8L8XTR1VZKIGRXHHR1L5T3R60WF8O5',1);
COMMIT;
