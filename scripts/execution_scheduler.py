import csv
import os
projects = ["pancakeswap", "venus", "alpaca-finance", "biswap", "multichain", "pinksale", "coinwind", "unicrypt", "wombat-exchange", "dxsale", "thena", "ankr", "helio-protocol", "wombex-finance", "stargate", "tranchess", "team-finance", "apeswap", "mdex", "beefy", "poly-network", "ellipsis-finance", "babydogeswap", "w3swap", "izumi-finance", "autofarm", "liqee", "tornado-cash", "belt-finance", "cbridge", "tokensfarm", "nomiswap", "dodo", "magpie", "babyswap", "apollox", "dforce", "portal", "acryptos", "planet", "pnetwork", "terra-bridge", "knightswap-finance", "deeplock", "dot-dot-finance", "wing-finance", "solo-top", "bunny", "valas-finance", "bakeryswap", "titano-swych", "moonfarm", "fstswap", "wrapped-bnb", "stader", "linear-finance", "synapse", "orion-protocol", "guard-helmet", "quoll", "kalata", "bolide", "ten-finance", "bifi", "level-finance", "hashflow", "nemesis-dao", "hector-network", "openleverage", "horizon-protocol", "burgerswap", "homora-v2", "woo-network", "kyberswap", "orbit-bridge",
            "smoothy", "pandora", "swapfish", "iotube", "cream-finance", "bscswap", "mars-ecosystem", "pacoca", "animal-farm", "grizzlyfi", "everrise", "definix", "nerve", "radioshack", "goose-finance", "bearn", "allbridge", "annex", "jetfuel-finance", "scientix", "kine-finance", "pstake", "revault", "btcst", "baryon-network", "hyper-finance", "gyro", "o3-swap", "alita-finance", "nest-protocol", "1inch-network", "cub-finance", "fortube", "atlantis-loans", "paraluni", "yoshi-exchange", "el-dorado-exchange", "depth", "meter-passport", "value-finance", "insurace", "empiredex", "spartan", "deri-protocol", "mux-protocol", "impossible-finance", "openocean", "rabbit-finance", "kalmy-app", "killswitch", "nftb", "kyotoswap", "swamp-finance", "coinswap-space", "julswap", "wineryswap", "mint-club", "wepiggy", "leonicornswap", "sushi", "templar-dao", "jetswap", "usd+", "hyphen", "rbx", "Dinosaur Eggs", "Aequinox", "DOOAR", "DAO Maker", "Connext", "Waterfall DeFi", "Sphynx", "XEUS", "PinkSwap", "CrossChain Bridge"]

addrs = ["0xf4c8e32eadec4bfe97e0f595add0f4450a863a11",
         "0x86069feb223ee303085a1a505892c9d4bdbee996",
         "0x406ec2705f1399d25801bd86b7d8d69ab9a91ab9",
         "0xfbbf371c9b0b994eebfcc977cef603f7f31c070d",
         "0xf780fde07fa56a881fb9566c7bdf9653471ac70a",
         "0x34b897289fccb43c048b2cea6405e840a129e021",
         "0x8b9ca04656a74e218ecbd444c493872d19533e06",
         "0xe9fe83aa430ace4b703c299701142f9dfdde730e",
         "0xf04ca87fe55f413b027ce01d8c9dcd662495fed4",
         "0x7144851e51523a88ea6bec9710cc07f3a9b3baa7",
         "0xcfe13d138d6471b827528b077eadc9330b9fad78",
         "0x2Af749593978CB79Ed11B9959cD82FD128BA4f8d",
         "0xe58e64fb76e3c3246c34ee596fb8da300b5adfbb",
         "0x20a304a7d126758dfe6b243d0fc515f83bca8431",
         "0x14cbeee51410c4e3b8269b534933404aee416a96",
         "0x62ee96e6365ab515ec647c065c2707d1122d7b26",
         "0x2b01fc6b1b3f4ff60f2d9fcab5af8f298f3d6fb9",
         "0xc31c0993706b0da60f04aa9c9e72812c0ca7b274",
         "0x86069feb223ee303085a1a505892c9d4bdbee996",
         "0xafd89d21bdb66d00817d4153e055830b1c2b3970"]


def store_csv(file_name, data, path="scripts/output/"):
    full_path = path+file_name
    if os.path.isfile(full_path):
        mode = "a"
    else:
        mode = "w+"
    with open(full_path, mode, newline="") as file:
        for line in data:
            # write the data to the file
            file.write(line.__repr__()+"\n")
