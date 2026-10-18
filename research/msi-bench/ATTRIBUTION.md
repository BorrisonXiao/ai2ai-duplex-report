# MSI-Bench Audio Attribution

This file lists the provenance and licenses of all third-party audio material
contained in the MSI-Bench release package. Two sources are used: Mozilla
Common Voice 17.0 (speaker reference clips for voice cloning) and Freesound
(background ambience). No other third-party audio is present in the released
waveforms.

## Speech voices — Mozilla Common Voice 17.0

All dialogue speech is synthesized. The synthetic voices were created by voice
cloning from reference clips in
[Mozilla Common Voice 17.0](https://commonvoice.mozilla.org/) (accessed via the
`fsicoli/common_voice_17_0` Hugging Face mirror): 96 cloned voices in total,
48 English and 48 Chinese (zh-CN). Common Voice is released under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/); contributors are anonymous
and no attribution is required. No original Common Voice recording is
redistributed in this package; only cloned synthetic speech derived from them.

## Background ambience — Freesound

The 74 ambience recordings below were sourced from
[Freesound](https://freesound.org/): 49 under CC0 1.0, 21 under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), 4 under
[CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). None carry
NonCommercial or NoDerivatives terms.

**Modifications.** Each recording was converted to mono 24 kHz,
loudness-normalized, randomly cropped to the dialogue duration, attenuated, and mixed
beneath the synthesized dialogue. The `acoustic_asset_id` field of each case
identifies the recording used (the trailing `fs<id>` is the Freesound sound id).

| # | Freesound sound | Author | License | `acoustic_asset_id` |
|---|---|---|---|---|
| 1 | [Airplane cabin ambience / atmosphere Airbus A330-300](https://freesound.org/people/FillSoko/sounds/456092/) | FillSoko | CC0 1.0 | `airplane_cabin__airbus_a330_300_cabin_ambience__fs456092` |
| 2 | [Airplane_Cabine ambiance (during flight).wav](https://freesound.org/people/Mar.Sounds/sounds/627056/) | Mar.Sounds | CC0 1.0 | `airplane_cabin__airplane_cabine_ambiance_during_flight_wav__fs627056` |
| 3 | [Classroom Connected.aif](https://freesound.org/people/theniteowls/sounds/144081/) | theniteowls | CC0 1.0 | `art_studio__classroom_connected_aif__fs144081` |
| 4 | [crowd int large young chatty lecture room ISNA open mic.flac](https://freesound.org/people/kyles/sounds/451597/) | kyles | CC0 1.0 | `auditorium__crowd_int_large_young_chatty_lecture_room_isna_open_mic_fl__fs451597` |
| 5 | [people_in_big_hall_ambiance_001.wav](https://freesound.org/people/Martina_Leitschuh/sounds/582944/) | Martina_Leitschuh | CC BY 4.0 | `auditorium__people_in_big_hall_ambiance_001_wav__fs582944` |
| 6 | [Summer Backyard Ambience.wav](https://freesound.org/people/180156/sounds/445509/) | 180156 | CC BY 3.0 | `backyard__summer_backyard_wav__fs445509` |
| 7 | [Inside Bakery, Shop Ambience, Day, London, 2OA - Spatial Audio](https://freesound.org/people/VizAion/sounds/802509/) | VizAion | CC0 1.0 | `bakery__inside_bakery_shop_ambience_day_london_2oa_spatial_audio__fs802509` |
| 8 | [Ambience Bank Kookmin Bank.wav](https://freesound.org/people/tweeterdj/sounds/30469/) | tweeterdj | CC BY 3.0 | `banking__ambience_bank_kookmin_bank_wav__fs30469` |
| 9 | [room-tone bedroom 757 PM 240215_0664](https://freesound.org/people/klankbeeld/sounds/735342/) | klankbeeld | CC BY 4.0 | `bedroom__room_tone_bedroom_757_pm_240215_0664__fs735342` |
| 10 | [room tone small trailer bedroom night quiet with distant highway traffic.flac](https://freesound.org/people/kyles/sounds/451181/) | kyles | CC0 1.0 | `bedroom__room_tone_small_trailer_bedroom_night_quiet_with_distant__fs451181` |
| 11 | [Bus_Interior_Commuting_Hong_Kong](https://freesound.org/people/ivoliYT/sounds/723833/) | ivoliYT | CC0 1.0 | `bus_cabin__bus_interior_commuting_hong_kong__fs723833` |
| 12 | [bus_interior_highway_2.WAV](https://freesound.org/people/ivolipa/sounds/264440/) | ivolipa | CC0 1.0 | `bus_cabin__bus_interior_highway_2_wav__fs264440` |
| 13 | [Interior - Car - State Street - Pendleton, Indiana - During Rain](https://freesound.org/people/thestoryshop/sounds/251491/) | thestoryshop | CC0 1.0 | `car_cabin__interior_car_state_street_pendleton_indiana_rain__fs251491` |
| 14 | [3. Ambience interior car windy.wav](https://freesound.org/people/btherad2000/sounds/328048/) | btherad2000 | CC BY 4.0 | `car_cabin__interior_car_windy_wav__fs328048` |
| 15 | [Medical Waiting Room Ambience](https://freesound.org/people/mht23SD/sounds/707881/) | mht23SD | CC0 1.0 | `car_rental_desk__medical_waiting_room_ambience__fs707881` |
| 16 | [City Park ambience Casinotuin Ht 190610_0025.flac](https://freesound.org/people/klankbeeld/sounds/474807/) | klankbeeld | CC BY 4.0 | `city_parks__city_park_casinotuin_ht_190610_0025__fs474807` |
| 17 | [Moscow, Tsaritsyno Park ambience XY mics.wav](https://freesound.org/people/gladkiy/sounds/348860/) | gladkiy | CC0 1.0 | `city_parks__moscow_tsaritsyno_park_xy_mics__fs348860` |
| 18 | [Classroom Ambience (before class)](https://freesound.org/people/aldy505/sounds/403928/) | aldy505 | CC BY 4.0 | `classroom__classroom_ambience_before_class__fs403928` |
| 19 | [hospital ambience indoor medical clinic waiting room](https://freesound.org/people/jerry.berumen/sounds/762124/) | jerry.berumen | CC BY 4.0 | `clinic_room__hospital_indoor_medical_clinic_waiting_room__fs762124` |
| 20 | [MS STEREO Coffee Shop, 6 People, low chatter, refrigerator, barista movement 1.WAV](https://freesound.org/people/AwenAudio/sounds/403065/) | AwenAudio | CC0 1.0 | `coffee_shop__ms_stereo_coffee_shop_6_people_low_chatter_refrigerator__fs403065` |
| 21 | [MS-STEREO Coffee Shop, 6 People, low chatter, refrigerator,  barista making milk shake, customers entering 3.WAV](https://freesound.org/people/AwenAudio/sounds/403066/) | AwenAudio | CC0 1.0 | `coffee_shop__ms_stereo_coffee_shop_6_people_low_chatter_refrigerator__fs403066` |
| 22 | [Medium sized crowd (around 100 people) chatting in a small hall.wav](https://freesound.org/people/arpeggio1980/sounds/523395/) | arpeggio1980 | CC0 1.0 | `community_center__medium_crowd_chatting_small_community_hall__fs523395` |
| 23 | [indoors house dorm dormitory ambient room tone distant motor.wav](https://freesound.org/people/bulbastre/sounds/126937/) | bulbastre | CC BY 4.0 | `dormitory__indoors_house_dorm_dormitory_ambient_room_tone_distant_mot__fs126937` |
| 24 | [indoors house dorm dormitory ambient room tone with halfway open window traffic.wav](https://freesound.org/people/bulbastre/sounds/126938/) | bulbastre | CC BY 4.0 | `dormitory__indoors_house_dorm_dormitory_ambient_room_tone_with_halfwa__fs126938` |
| 25 | [Laundromat Ambience.wav](https://freesound.org/people/ruthdt98/sounds/408307/) | ruthdt98 | CC0 1.0 | `dry_cleaner__laundromat_ambience_wav__fs408307` |
| 26 | [forest farmland 1219 PM 220503_0341.flac](https://freesound.org/people/klankbeeld/sounds/632420/) | klankbeeld | CC BY 4.0 | `elder_care_room__forest_farmland_1219_pm_220503_0341_flac__fs632420` |
| 27 | [snow ambience suburb 130115_01 130115_02.flac](https://freesound.org/people/klankbeeld/sounds/174350/) | klankbeeld | CC BY 4.0 | `elder_care_room__snow_suburb_130115_01_130115_02_flac__fs174350` |
| 28 | [General Fusion industrial workshop factory ambience11 overlooking factory floor.wav](https://freesound.org/people/kyles/sounds/450117/) | kyles | CC0 1.0 | `factory_floor__general_fusion_overlooking_factory_floor__fs450117` |
| 29 | [G16-09-Factory-Overhead Crane.wav](https://freesound.org/people/craigsmith/sounds/438133/) | craigsmith | CC0 1.0 | `factory_floor__large_factory_work_floor_overhead_crane__fs438133` |
| 30 | [S13-06 Crowd walla at outdoor farmers’ market.wav](https://freesound.org/people/craigsmith/sounds/675026/) | craigsmith | CC0 1.0 | `farmers_market_stall__s13_06_crowd_walla_at_outdoor_farmers_market_wav__fs675026` |
| 31 | [columbia road flower market.wav](https://freesound.org/people/Noise%20Cuisine/sounds/46879/) | Noise Cuisine | CC BY 4.0 | `florist_shop__columbia_road_flower_market_wav__fs46879` |
| 32 | [Flower Market Columbia Road.wav](https://freesound.org/people/petewyer2/sounds/345598/) | petewyer2 | CC0 1.0 | `florist_shop__flower_market_columbia_road_wav__fs345598` |
| 33 | [Interior Salão de Jogos](https://freesound.org/people/sons_pt/sounds/241446/) | sons_pt | CC BY 4.0 | `game_table__interior_salao_de_jogos__fs241446` |
| 34 | [room tone garage full of junk with heavy distant highway traffic country2.flac](https://freesound.org/people/kyles/sounds/451174/) | kyles | CC0 1.0 | `garage__room_tone_garage_full_of_junk_with_heavy_distant_highway__fs451174` |
| 35 | [Gym ambience -- busy American gym](https://freesound.org/people/logancircle2/sounds/503161/) | logancircle2 | CC BY 4.0 | `gym__gym_ambience_busy_american_gym__fs503161` |
| 36 | [Gym / Fitness Facility Ambience](https://freesound.org/people/DAVESTALKER/sounds/248247/) | DAVESTALKER | CC0 1.0 | `gym__gym_fitness_facility_ambience__fs248247` |
| 37 | [Barber shop interior, empty room with air conditioning blowing, clock tictac and road hum outside](https://freesound.org/people/felix.blume/sounds/706411/) | felix.blume | CC0 1.0 | `hair_salon__barber_shop_interior_empty_room_with_air_conditioning_bl__fs706411` |
| 38 | [HOSPITAL - LONG CORRIDOR - ATMO / AMB (01)](https://freesound.org/people/tferrino/sounds/618354/) | tferrino | CC0 1.0 | `hospital__hospital_long_corridor_atmo_amb_01__fs618354` |
| 39 | [220130_Asuncion_LobbyHotelGuarani_Morning](https://freesound.org/people/blaukreuz/sounds/747196/) | blaukreuz | CC0 1.0 | `hotel__220130_asuncion_lobbyhotelguarani_morning__fs747196` |
| 40 | [AMB_Recepcion_detras_escaleras_250508](https://freesound.org/people/Dani_S.T./sounds/805983/) | Dani_S.T. | CC0 1.0 | `hotel__amb_recepcion_detras_escaleras_250508__fs805983` |
| 41 | [Apartment kitchen ambience](https://freesound.org/people/AlexLane/sounds/459843/) | AlexLane | CC0 1.0 | `kitchen__apartment_kitchen_ambience__fs459843` |
| 42 | [Siemens Dishwasher – Kitchen Ambience & Spatial Machine Character (LCT‑040 XY, 96 kHz) - 240220_009_Tr1_2](https://freesound.org/people/TSP-Talk/sounds/845626/) | TSP-Talk | CC0 1.0 | `kitchen__siemens_dishwasher_kitchen_ambience_spatial_machine_char__fs845626` |
| 43 | [RoomTone05](https://freesound.org/people/richwise/sounds/474829/) | richwise | CC0 1.0 | `laboratory__roomtone05__fs474829` |
| 44 | [washing machine 02](https://freesound.org/people/oliwoli/sounds/548460/) | oliwoli | CC0 1.0 | `laundry_area__washing_machine_02__fs548460` |
| 45 | [20121112 TU Delft Library, quiet study room - general ambience.wav](https://freesound.org/people/el_mar/sounds/171006/) | el_mar | CC BY 3.0 | `library__20121112_tu_delft_library_quiet_study_room_general_ambienc__fs171006` |
| 46 | [Room-tone apartment radio 191020_0081.flac](https://freesound.org/people/klankbeeld/sounds/495865/) | klankbeeld | CC BY 4.0 | `living_room__background_tv_next_room_apartment_room_tone__fs495865` |
| 47 | [Living Room Ambience, Children Playing Outside, Clock Ticking - Halifax, NS](https://freesound.org/people/Podel1/sounds/803302/) | Podel1 | CC BY 4.0 | `living_room__living_room_ambience_children_playing_outside_clock_tick__fs803302` |
| 48 | [Broken Tv in the background.wav](https://freesound.org/people/Jordishaw/sounds/490749/) | Jordishaw | CC BY 4.0 | `media_room__broken_tv_in_the_background_wav__fs490749` |
| 49 | [movietheatreambience.mp3](https://freesound.org/people/NoiseCollector/sounds/73336/) | NoiseCollector | CC BY 3.0 | `media_room__movietheatreambience_mp3__fs73336` |
| 50 | [adults_gathering_for_meeting.wav](https://freesound.org/people/joedeshon/sounds/118852/) | joedeshon | CC BY 4.0 | `meeting_room__adults_gathering_for_meeting__fs118852` |
| 51 | [Suburban hospital ambience - Moscow region, mostly old ladies & gents calmly talking and walking around, door closes, general noises XY mics .wav](https://freesound.org/people/gladkiy/sounds/348109/) | gladkiy | CC0 1.0 | `nursing_station__suburban_hospital_moscow_region_mostly_old_ladies_gents__fs348109` |
| 52 | [Suburban hospital ambience - Moscow region, mostly old ladies & gents calmly talking and walking around, door closes, general noises OMNI mics.wav](https://freesound.org/people/gladkiy/sounds/348110/) | gladkiy | CC0 1.0 | `nursing_station__suburban_hospital_moscow_region_mostly_old_ladies_gents__fs348110` |
| 53 | [The Office](https://freesound.org/people/qubodup/sounds/211945/) | qubodup | CC BY 4.0 | `open_office__busy_office_soundscape__fs211945` |
| 54 | [Office Ambience](https://freesound.org/people/qubodup/sounds/199896/) | qubodup | CC BY 4.0 | `open_office__office_ambience_printer_typing_people__fs199896` |
| 55 | [Party-People indoor 01 -  calm, relaxed (german)](https://freesound.org/people/Pfannkuchn/sounds/457604/) | Pfannkuchn | CC0 1.0 | `party_room__party_people_indoor_01_calm_relaxed_german__fs457604` |
| 56 | [Party-People indoor 02 - lively, louder (german)](https://freesound.org/people/Pfannkuchn/sounds/457605/) | Pfannkuchn | CC0 1.0 | `party_room__party_people_indoor_02_lively_louder_german__fs457605` |
| 57 | [Inside a pharmacy. AMB. OWI.wav](https://freesound.org/people/the_Carlos/sounds/706971/) | the_Carlos | CC BY 4.0 | `pharmacy__inside_a_pharmacy_amb_owi_wav__fs706971` |
| 58 | [Pharmacy](https://freesound.org/people/Elizabethmoimane/sounds/766036/) | Elizabethmoimane | CC0 1.0 | `pharmacy__pharmacy__fs766036` |
| 59 | [Entrance Area Busy Museum Ludwig Köln Germany](https://freesound.org/people/qubodup/sounds/859384/) | qubodup | CC0 1.0 | `public_museums__entrance_area_busy_museum_ludwig_koln__fs859384` |
| 60 | [Main Lobby Busy Museum Ludwig Köln Germany](https://freesound.org/people/qubodup/sounds/859385/) | qubodup | CC0 1.0 | `public_museums__main_lobby_busy_museum_ludwig_koln__fs859385` |
| 61 | [ambience - restaurant.WAV](https://freesound.org/people/soundtracvkradio/sounds/394678/) | soundtracvkradio | CC0 1.0 | `restaurant__ambience_restaurant_wav__fs394678` |
| 62 | [Resturant Ambience Tandoori.mp3](https://freesound.org/people/digifishmusic/sounds/33392/) | digifishmusic | CC BY 4.0 | `restaurant__restaurant_ambience_tandoori_mp3__fs33392` |
| 63 | [brazilian office ambience.mp3](https://freesound.org/people/_vk/sounds/221848/) | _vk | CC0 1.0 | `shelter_intake_desk__brazilian_notary_office_waiting_line__fs221848` |
| 64 | [Minneapolis Post Office Ambience.MP3](https://freesound.org/people/emilyzitek/sounds/673343/) | emilyzitek | CC0 1.0 | `shelter_intake_desk__minneapolis_post_office_ambience__fs673343` |
| 65 | [Bar room background 2.wav](https://freesound.org/people/itinerantmonk108/sounds/641622/) | itinerantmonk108 | CC0 1.0 | `sports_club_lounge__bar_room_background_2_wav__fs641622` |
| 66 | [ambience, city, metro, Komsomolskaya, subway, Moscow](https://freesound.org/people/AlexanderChe/sounds/727841/) | AlexanderChe | CC0 1.0 | `station__komsomolskaya_subway_station_moscow__fs727841` |
| 67 | [AMBIENCE_INTERIOR_TRAIN-STATION_LISBOA_SANTA-APOLONIA_4824_01](https://freesound.org/people/pblzr/sounds/785389/) | pblzr | CC0 1.0 | `station__train_station_lisboa_santa_apolonia_01__fs785389` |
| 68 | [AMBPubl-Samsung Galaxy Smartphone, CU_Grocery Store, Checkout Counter, Footsteps, Beeps, Groceries_Nicholas Judy_TDC](https://freesound.org/people/designerschoice/sounds/825994/) | designerschoice | CC0 1.0 | `store__ambpubl_samsung_galaxy_smartphone_cu_grocery_store_check__fs825994` |
| 69 | [Grocery Store Ambience Checkout Line](https://freesound.org/people/deleted_user_7146007/sounds/383718/) | deleted_user_7146007 | CC0 1.0 | `store__grocery_store_ambience_checkout_line__fs383718` |
| 70 | [Moscow subway train ride - interior ambience - Kaluzhsko-Rizhskaya subway line OMNI mics.flac](https://freesound.org/people/gladkiy/sounds/333944/) | gladkiy | CC0 1.0 | `train_carriage__moscow_subway_train_ride_interior_omni__fs333944` |
| 71 | [Moscow subway train ride - interior ambience - Kaluzhsko-Rizhskaya subway line XY mics.flac](https://freesound.org/people/gladkiy/sounds/333943/) | gladkiy | CC0 1.0 | `train_carriage__moscow_subway_train_ride_interior_xy__fs333943` |
| 72 | [Office Ambience 01 OWI.wav](https://freesound.org/people/DavidFrbr/sounds/327497/) | DavidFrbr | CC0 1.0 | `travel_agency__office_ambience_01_owi_wav__fs327497` |
| 73 | [Walking through City 2](https://freesound.org/people/NachtmahrTV/sounds/553246/) | NachtmahrTV | CC0 1.0 | `walking__walking_through_city_2__fs553246` |
| 74 | [Walking through City](https://freesound.org/people/NachtmahrTV/sounds/553247/) | NachtmahrTV | CC0 1.0 | `walking__walking_through_city__fs553247` |
