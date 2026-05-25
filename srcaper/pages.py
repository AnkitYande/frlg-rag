#Bubapedia Walkthrough Pages
SEED_PAGES = [f"Walkthrough:Pokémon FireRed and LeafGreen/Part {i}" for i in range(1, 21)]

# Serebii Route Pages
SEREBII_BASE = "https://www.serebii.net"
SEREBII_ROUTE_BASE = f"{SEREBII_BASE}/pokearth/kanto/3rd"

# All Kanto locations for Gen III (FireRed/LeafGreen)
SEREBII_ROUTE_URLS = (
    [f"{SEREBII_ROUTE_BASE}/route{n}.shtml" for n in range(1, 26)] +
    [
        f"{SEREBII_ROUTE_BASE}/ceruleancave.shtml",
        f"{SEREBII_ROUTE_BASE}/ceruleancity.shtml",
        f"{SEREBII_ROUTE_BASE}/cinnabarisland.shtml",
        f"{SEREBII_ROUTE_BASE}/celadoncity.shtml",
        f"{SEREBII_ROUTE_BASE}/diglett'scave.shtml",
        f"{SEREBII_ROUTE_BASE}/fuchsiacity.shtml",
        f"{SEREBII_ROUTE_BASE}/indigoplateau.shtml",
        f"{SEREBII_ROUTE_BASE}/lavendertown.shtml",
        f"{SEREBII_ROUTE_BASE}/mt.moon.shtml",
        f"{SEREBII_ROUTE_BASE}/pallettown.shtml",
        f"{SEREBII_ROUTE_BASE}/pewtercity.shtml",
        f"{SEREBII_ROUTE_BASE}/pokemonmansion.shtml",
        f"{SEREBII_ROUTE_BASE}/pokemontower.shtml",
        f"{SEREBII_ROUTE_BASE}/powerplant.shtml",
        f"{SEREBII_ROUTE_BASE}/rocktunnel.shtml",
        f"{SEREBII_ROUTE_BASE}/rockethideout.shtml",
        f"{SEREBII_ROUTE_BASE}/safarizone.shtml",
        f"{SEREBII_ROUTE_BASE}/saffroncity.shtml",
        f"{SEREBII_ROUTE_BASE}/seafoamislands.shtml",
        f"{SEREBII_ROUTE_BASE}/silphco.shtml",
        f"{SEREBII_ROUTE_BASE}/ssanne.shtml",
        f"{SEREBII_ROUTE_BASE}/undergroundpath5-6.shtml",
        f"{SEREBII_ROUTE_BASE}/undergroundpath7-8.shtml",
        f"{SEREBII_ROUTE_BASE}/vermilioncity.shtml",
        f"{SEREBII_ROUTE_BASE}/victoryroad.shtml",
        f"{SEREBII_ROUTE_BASE}/viridiancity.shtml",
        f"{SEREBII_ROUTE_BASE}/viridianforest.shtml",
        # Sevii Islands
        f"{SEREBII_ROUTE_BASE}/oneisland.shtml",
        f"{SEREBII_ROUTE_BASE}/kindleroad.shtml",
        f"{SEREBII_ROUTE_BASE}/treasurebeach.shtml",
        f"{SEREBII_ROUTE_BASE}/mt.ember.shtml",
        f"{SEREBII_ROUTE_BASE}/twoisland.shtml",
        f"{SEREBII_ROUTE_BASE}/capebrink.shtml",
        f"{SEREBII_ROUTE_BASE}/threeisland.shtml",
        f"{SEREBII_ROUTE_BASE}/threeisleport.shtml",
        f"{SEREBII_ROUTE_BASE}/threeislepath.shtml",
        f"{SEREBII_ROUTE_BASE}/bondbridge.shtml",
        f"{SEREBII_ROUTE_BASE}/berryforest.shtml",
        f"{SEREBII_ROUTE_BASE}/fourisland.shtml",
        f"{SEREBII_ROUTE_BASE}/icefallcave.shtml",
        f"{SEREBII_ROUTE_BASE}/fiveisland.shtml",
        f"{SEREBII_ROUTE_BASE}/fiveislemeadow.shtml",
        f"{SEREBII_ROUTE_BASE}/memorialpillar.shtml",
        f"{SEREBII_ROUTE_BASE}/waterlabyrinth.shtml",
        f"{SEREBII_ROUTE_BASE}/resortgorgeous.shtml",
        f"{SEREBII_ROUTE_BASE}/rocketwarehouse.shtml",
        f"{SEREBII_ROUTE_BASE}/lostcave.shtml",
        f"{SEREBII_ROUTE_BASE}/sixisland.shtml",
        f"{SEREBII_ROUTE_BASE}/waterpath.shtml",
        f"{SEREBII_ROUTE_BASE}/ruinvalley.shtml",
        f"{SEREBII_ROUTE_BASE}/dottedhole.shtml",
        f"{SEREBII_ROUTE_BASE}/greenpath.shtml",
        f"{SEREBII_ROUTE_BASE}/patternbush.shtml",
        f"{SEREBII_ROUTE_BASE}/outcastisland.shtml",
        f"{SEREBII_ROUTE_BASE}/alteringcave.shtml",
        f"{SEREBII_ROUTE_BASE}/sevenisland.shtml",
        f"{SEREBII_ROUTE_BASE}/trainertower.shtml",
        f"{SEREBII_ROUTE_BASE}/canyonentrance.shtml",
        f"{SEREBII_ROUTE_BASE}/sevaultcanyon.shtml",
        f"{SEREBII_ROUTE_BASE}/tanobyruins.shtml",
        f"{SEREBII_ROUTE_BASE}/navelrock.shtml",
        f"{SEREBII_ROUTE_BASE}/birthisland.shtml",
    ]
)

# Serebii Gen 1 Pokédex pages (001–151)
SEREBII_POKEMON_URLS = [
    f"{SEREBII_BASE}/pokedex-rs/{str(n).zfill(3)}.shtml"
    for n in range(1, 152)
]