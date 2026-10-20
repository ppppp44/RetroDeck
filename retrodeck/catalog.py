from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CatalogSystem:
    system_id: str
    name: str
    manufacturer: str
    category: str
    era: str
    aliases: tuple[str, ...]
    extensions: tuple[str, ...]
    core_hints: tuple[str, ...]
    verified: bool = True
    notes: str = ''

# The catalog is intentionally metadata-driven. Core availability is determined at runtime;
# these are compatibility associations, not claims that every core is installed.
_RAW = [
('nes','NES / Famicom','Nintendo','Nintendo consoles','1983–1995','nes,famicom','nes,zip','nestopia,mesen'),
('snes','SNES / Super Famicom','Nintendo','Nintendo consoles','1990–2003','snes,super famicom','sfc,smc,fig,zip','snes9x,bsnes'),
('n64','Nintendo 64','Nintendo','Nintendo consoles','1996–2003','n64,nintendo64','n64,z64,v64','mupen64plus,next'),
('gamecube','GameCube','Nintendo','Nintendo consoles','2001–2007','gc,ngc','iso,gcm,rvz','dolphin',False,'Usually better served by standalone Dolphin.'),
('game_boy','Game Boy','Nintendo','Nintendo handhelds','1989–2003','gb','gb,zip','gambatte,mgba'),
('game_boy_color','Game Boy Color','Nintendo','Nintendo handhelds','1998–2003','gbc','gbc,zip','gambatte,mgba'),
('game_boy_advance','Game Boy Advance','Nintendo','Nintendo handhelds','2001–2008','gba','gba,zip','mgba'),
('nds','Nintendo DS','Nintendo','Nintendo handhelds','2004–2013','nds','nds','desmume,melonds'),
('virtual_boy','Virtual Boy','Nintendo','Nintendo handhelds','1995–1996','vb','vb','beetle_vb'),
('pokemon_mini','Pokémon mini','Nintendo','Nintendo handhelds','2001–2003','pokemon mini','min','pokemini'),
('fds','Famicom Disk System','Nintendo','Nintendo consoles','1986–1992','fds','fds','mesen'),
('satellaview','Satellaview','Nintendo','Nintendo consoles','1995–2000','bsx','bs,bsx','mednafen_supergrafx'),
('3ds','Nintendo 3DS','Nintendo','Nintendo handhelds','2011–2020','3ds','3ds,cia','citra',False,'Experimental; only usable when a compatible core is discovered.'),
('playstation','PlayStation','Sony','Sony PlayStation','1994–2006','ps1,psx','cue,bin,chd,iso,pbp','beetle_psx,pcsx_rearmed,duckstation'),
('psp','PlayStation Portable','Sony','Sony PlayStation','2004–2014','psp','iso,cso,pbp','ppsspp'),
('ps2','PlayStation 2','Sony','Sony PlayStation','2000–2013','ps2','iso,chd','play',False,'Use standalone PCSX2 unless a verified compatible core is present.'),
('sg1000','SG-1000','Sega','Sega consoles and handhelds','1983–1985','sg1000','sg,bin','genesis_plus_gx'),
('master_system','Master System','Sega','Sega consoles and handhelds','1985–1996','sms','sms,bin','genesis_plus_gx'),
('genesis','Genesis / Mega Drive','Sega','Sega consoles and handhelds','1988–1997','megadrive,md','md,gen,smd,bin','genesis_plus_gx,picodrive'),
('sega_cd','Sega CD / Mega-CD','Sega','Sega consoles and handhelds','1991–1996','megacd','cue,bin,chd,iso','genesis_plus_gx'),
('sega32x','Sega 32X','Sega','Sega consoles and handhelds','1994–1996','32x','32x,bin','picodrive'),
('game_gear','Game Gear','Sega','Sega consoles and handhelds','1990–1997','gg','gg,bin','genesis_plus_gx'),
('saturn','Sega Saturn','Sega','Sega consoles and handhelds','1994–2000','saturn','cue,bin,chd,iso','beetle_saturn,yabause'),
('dreamcast','Dreamcast','Sega','Sega consoles and handhelds','1998–2001','dc','gdi,cdi,chd,iso','flycast',False,'Requires a verified Flycast installation; not preconfigured.'),
('pico','Sega Pico','Sega','Sega consoles and handhelds','1993–1998','pico','bin','genesis_plus_gx'),
('naomi','Sega NAOMI','Sega','Arcade systems','1998–2005','naomi','zip,7z','flycast',False),
('atomiswave','Atomiswave','Sega','Arcade systems','2002–2009','atomiswave','zip,7z','flycast',False),
('atari2600','Atari 2600','Atari','Atari systems','1977–1992','2600,vcs','a26,bin','stella'),
('atari5200','Atari 5200','Atari','Atari systems','1982–1984','5200','a52,bin','atari800'),
('atari7800','Atari 7800','Atari','Atari systems','1986–1992','7800','a78,bin','prosystem'),
('lynx','Atari Lynx','Atari','Atari systems','1989–1994','lynx','lnx','handy'),
('jaguar','Atari Jaguar','Atari','Atari systems','1993–1996','jag','j64,rom','virtualjaguar'),
('atari_st','Atari ST','Atari','Computers and DOS','1985–1993','st,atarist','st,stx,msa','hatari'),
('atari8','Atari 8-bit family','Atari','Computers and DOS','1979–1992','atari8','atr,xex,car','atari800'),
('atari400','Atari 400/800','Atari','Computers and DOS','1979–1992','atari 400,atari 800','atr,xex','atari800'),
('atari_falcon','Atari Falcon','Atari','Computers and DOS','1992–1995','falcon','st,msa','hatari',False),
('pc_engine','PC Engine','NEC','NEC / PC Engine','1987–1994','pce','pce','mednafen_pce_fast,beetle_pce'),
('turbografx16','TurboGrafx-16','NEC','NEC / PC Engine','1987–1994','turbografx','pce','mednafen_pce_fast'),
('supergrafx','SuperGrafx','NEC','NEC / PC Engine','1989–1991','supergrafx','sgx','mednafen_supergrafx'),
('pce_cd','PC Engine CD','NEC','NEC / PC Engine','1988–1994','pcecd','cue,bin,chd','mednafen_pce'),
('turbografx_cd','TurboGrafx-CD','NEC','NEC / PC Engine','1988–1994','tgcd','cue,bin,chd','mednafen_pce'),
('pc_fx','PC-FX','NEC','NEC / PC Engine','1994–1998','pcfx','cue,ccd,bin','mednafen_pcfx'),
('neo_geo_aes','Neo Geo AES','SNK','SNK / Neo Geo','1990–2004','aes','zip,7z','fbneo,mame'),
('neo_geo_mvs','Neo Geo MVS','SNK','SNK / Neo Geo','1990–2004','mvs','zip,7z','fbneo,mame'),
('neo_geo_cd','Neo Geo CD','SNK','SNK / Neo Geo','1994–1999','neogeocd','cue,bin,iso,chd','neocd'),
('neo_geo_pocket','Neo Geo Pocket','SNK','SNK / Neo Geo','1998–2001','ngp','ngp','mednafen_ngp'),
('neo_geo_pocket_color','Neo Geo Pocket Color','SNK','SNK / Neo Geo','1999–2001','ngpc','ngc,ngp','mednafen_ngp'),
('wonderswan','WonderSwan','Bandai','Bandai and other consoles','1999–2003','ws','ws','mednafen_wswan'),
('wonderswan_color','WonderSwan Color','Bandai','Bandai and other consoles','2000–2003','wsc','wsc','mednafen_wswan'),
('sufami','Bandai Sufami Turbo','Bandai','Bandai and other consoles','1996–1998','sufami','st','snes9x'),
('gx4000','Amstrad GX4000','Amstrad','Bandai and other consoles','1990–1991','gx4000','cpr','cap32'),
('colecovision','ColecoVision','Coleco','Bandai and other consoles','1982–1985','coleco','col,rom','bluemsx'),
('intellivision','Intellivision','Mattel','Bandai and other consoles','1979–1990','intv','int,bin','freeintv'),
('odyssey2','Magnavox Odyssey² / Videopac','Magnavox','Bandai and other consoles','1978–1984','odyssey2,videopac','bin,rom','o2em'),
('vectrex','Vectrex','GCE','Bandai and other consoles','1982–1984','vectrex','vec','vecx'),
('channel_f','Fairchild Channel F','Fairchild','Bandai and other consoles','1976–1979','channel f','chf','freechaf'),
('bally','Bally Astrocade','Bally','Bandai and other consoles','1977–1984','astrocade','bin','mame'),
('arcadia','Emerson Arcadia 2001','Emerson','Bandai and other consoles','1982–1984','arcadia','bin','mame'),
('supervision','Watara Supervision','Watara','Bandai and other consoles','1992–1996','supervision','sv','potator'),
('arduboy','Arduboy','Arduboy','Other supported platforms','2016–present','arduboy','hex,bin','arduous'),
('dos','MS-DOS','Microsoft','DOS and PC platforms','1981–present','msdos,dos','exe,com,bat,zip','dosbox_pure,dosbox'),
('c64','Commodore 64','Commodore','Commodore and other home computers','1982–1994','c64','d64,t64,prg,crt','vice_x64'),
('vic20','Commodore VIC-20','Commodore','Commodore and other home computers','1980–1984','vic20','prg,crt','vice_xvic'),
('pet','Commodore PET','Commodore','Commodore and other home computers','1977–1982','pet','prg','vice_xpet'),
('amiga','Amiga','Commodore','Commodore and other home computers','1985–1996','amiga','adf,ipf,hdf','puae'),
('amiga_cd32','Amiga CD32','Commodore','Commodore and other home computers','1993–1994','cd32','cue,bin,iso','puae'),
('zx_spectrum','ZX Spectrum','Sinclair','Commodore and other home computers','1982–1992','spectrum','tzx,tap,z80,sna','fuse'),
('zx81','ZX81','Sinclair','Commodore and other home computers','1981–1984','zx81','p,81','eightyone'),
('amstrad_cpc','Amstrad CPC','Amstrad','Commodore and other home computers','1984–1990','cpc','dsk,cpr','cap32'),
('msx','MSX','Microsoft / ASCII','Commodore and other home computers','1983–1995','msx','rom,dsk,cas','bluemsx'),
('msx2','MSX2','Microsoft / ASCII','Commodore and other home computers','1985–1995','msx2','rom,dsk','bluemsx'),
('apple2','Apple II','Apple','Commodore and other home computers','1977–1993','apple ii','dsk,do,po','mame'),
('macintosh','Macintosh','Apple','Commodore and other home computers','1984–2001','mac','dsk,img','mini vmac',False),
('x68000','Sharp X68000','Sharp','Commodore and other home computers','1987–1993','x68000','dim,hdm,2hd','px68k'),
('pc98','PC-98','NEC','Commodore and other home computers','1982–2000','pc98','fdi,fdd,hdi','np2kai'),
('pc88','PC-88','NEC','Commodore and other home computers','1981–1990','pc88','d88,fdi','quasi88'),
('sam_coupe','Sam Coupé','MGT','Commodore and other home computers','1989–1992','sam coupe','mgt,dsk','simcoupe'),
('oric','Oric','Tangerine','Commodore and other home computers','1983–1985','oric','dsk,tap','oric'),
('bbc_micro','BBC Micro','Acorn','Commodore and other home computers','1981–1994','bbc','ssd,dsd','mess'),
('acorn_electron','Acorn Electron','Acorn','Commodore and other home computers','1983–1986','electron','uef,ssd','mess'),
('dragon','Dragon 32/64','Dragon Data','Commodore and other home computers','1982–1984','dragon','dsk,cas','xroar'),
('trs80','TRS-80','Tandy','Commodore and other home computers','1977–1981','trs80','dsk,cas','mess'),
('ti83','TI-83 / TI-84','Texas Instruments','Commodore and other home computers','1996–present','ti83,ti84','8xp','tilp'),
('mame','MAME arcade','Multiple','Arcade systems','1975–present','arcade,mame','zip,7z','mame'),
('fbneo','FinalBurn Neo arcade','Multiple','Arcade systems','1978–present','fbneo,finalburn','zip,7z','fbneo'),
('fba','FB Alpha-compatible systems','Multiple','Arcade systems','1978–present','fba','zip,7z','fbneo'),
('cps1','CPS-1','Capcom','Arcade systems','1988–1995','cps1','zip,7z','fbneo,mame'),
('cps2','CPS-2','Capcom','Arcade systems','1993–2003','cps2','zip,7z','fbneo,mame'),
('cps3','CPS-3','Capcom','Arcade systems','1996–2003','cps3','zip,7z','fbneo,mame'),
('neo_geo_arcade','Neo Geo arcade','SNK','Arcade systems','1990–2004','neo geo arcade','zip,7z','fbneo,mame'),
('sega_system16','Sega System 16','Sega','Arcade systems','1985–1990','system16','zip,7z','fbneo,mame'),
('scummvm','ScummVM adventure games','Multiple','Arcade systems','1980–present','scummvm','scummvm,zip','scummvm'),
('tic80','TIC-80','TIC-80','Other supported platforms','2015–present','tic80','tic','tic80'),
('pico8','PICO-8','Lexaloffle','Other supported platforms','2015–present','pico8','p8','retro8',False),
('wasm4','WASM-4','WASM-4','Other supported platforms','2021–present','wasm4','wasm','wasm4'),
('chip8','CHIP-8','Multiple','Other supported platforms','1977–present','chip8','ch8,c8','turbografx'),
('uzebox','Uzebox','Uzebox','Other supported platforms','2008–present','uzebox','uze','uzebox'),
('zx_next','ZX Spectrum Next','Sinclair','Commodore and other home computers','2017–present','zx next','nex','fuse',False),
('coleco_adam','Coleco ADAM','Coleco','Commodore and other home computers','1983–1985','adam','ddp','mess'),
('laserdisc','LaserDisc arcade','Multiple','Arcade systems','1983–1995','laserdisk','daphne','hypseus'),
('sega_sg1000','Sega SG-1000 Mark III','Sega','Sega consoles and handhelds','1985–1989','sg mark iii','sms','genesis_plus_gx'),
('psx_arcade','PlayStation arcade','Sony','Arcade systems','1994–2000','ps arcade','bin,iso','beetle_psx'),
('gamepark','GP32','GamePark','Other supported platforms','2001–2005','gp32','smc','gpsp',False),
('jaguar_cd','Atari Jaguar CD','Atari','Atari systems','1995–1996','jaguar cd','cue,bin','virtualjaguar',False),
]
CATALOG = tuple(CatalogSystem(sid,n,m,c,e,tuple(a.split(',')),tuple('.'+x.strip().lstrip('.') for x in ex.split(',')),tuple(h.split(',')),v,notes) for sid,n,m,c,e,a,ex,h,*rest in _RAW for v,notes in [(rest[0] if rest else True, rest[1] if len(rest)>1 else '')])
CATALOG_BY_ID = {s.system_id:s for s in CATALOG}

def categories(): return sorted({s.category for s in CATALOG})
def search_catalog(text='', category='', installed_ids=None, favorites=None):
    text=text.casefold().strip(); installed_ids=installed_ids or set(); favorites=favorites or set()
    out=[]
    for s in CATALOG:
        hay=' '.join((s.name,s.manufacturer,s.category,s.system_id,*s.aliases)).casefold()
        if text and text not in hay: continue
        if category and s.category != category: continue
        out.append(s)
    return out
