import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from twitter import TweetPostman

MEDIAS_DIR = Path("medias")
MEDIAS_DIR.mkdir(exist_ok=True)

palette = {
    'contre': '#d93126',
    'pour': '#26d978',
    'abstentions': '#A8B9E8',
    'nonVotants': '#959595',
    'total': '#2663d9',
}


class VoteAnalysis:
    file: Path
    media_dir: Path

    def __init__(self, file: str | Path):
        self.file = Path(file) if isinstance(file, str) else file
        self.scrutin = json.loads(self.file.read_text())['scrutin']
        self.media_dir = MEDIAS_DIR.joinpath(self.uid)
        self.media_dir.mkdir(exist_ok=True)

    def __str__(self):
        return "\n".join([
            f"{self.date_scrutin}: {self.full_title}",
            self.synthese,
            '#DirectAN'
        ])

    @property
    def uid(self):
        return self.scrutin['uid']

    def build_pie(self):
        votes = self.scrutin['syntheseVote']['decompte']
        del votes['nonVotantsVolontaires']

        f, ax = plt.subplots(figsize=(6, 6))

        labels, values = zip(*votes.items())
        plt.pie(values, labels=labels, colors=[palette[l] for l in labels], autopct='%.0f%%')
        ax.set(xlabel="Répartition des choix au vote")

        total_pie_path = self.media_dir.joinpath("total_pie.png")
        plt.savefig(total_pie_path)
        plt.clf()
        return total_pie_path

    def build_bar(self):
        graph_cols: list[str] = ['pour', 'contre', 'abstentions', 'nonVotants']

        result = [{
            'name': 'total',
            'total': float(self.scrutin['syntheseVote']['nombreVotants']),
            **self.scrutin['syntheseVote']['decompte']
        }]

        for x in self.scrutin['ventilationVotes']['organe']['groupes']['groupe']:
            nb_membre = x['nombreMembresGroupe']
            votes = x['vote']['decompteVoix']
            result.append({'name': x['organeRef'], 'total': float(nb_membre), **votes})

        df = pd.DataFrame(result)
        del df['nonVotantsVolontaires']

        for col in graph_cols:
            df[col] = 100 * df[col].astype(float) / df['total']
        df['total'] = 100

        print(df)

        sns.set_theme(style="whitegrid")
        f, ax = plt.subplots(figsize=(12, 8))

        sns.barplot(x="total", y="name", data=df, label="Total", color=palette['total'])

        cumul = pd.Series([0] * len(df))
        for col in graph_cols:
            df[col + "_cumul"] = df[col] + cumul
            cumul = df[col + "_cumul"].copy()

        for col in reversed(graph_cols):
            sns.barplot(x=col + "_cumul", y="name", data=df, label=col, color=palette[col])

        ax.legend(ncol=2, loc="lower right", frameon=True)
        ax.set(xlim=(0, 100), ylabel="", xlabel="Répartition des choix au vote, par groupe parlementaire")
        sns.despine(left=True, bottom=True)

        all_bar_path = self.media_dir.joinpath("all_bar.png")
        plt.savefig(all_bar_path)
        plt.clf()

        return all_bar_path

    @property
    def full_title(self):
        return f"{self.scrutin['sort']['libelle'].replace('Assemblée nationale', '@AssembleeNat')} " \
               f"{self.scrutin['titre']}"

    @property
    def demandeur(self):
        return f"(Par {self.scrutin['demandeur']['texte']})"

    @property
    def date_scrutin(self):
        return '/'.join(reversed(self.scrutin['dateScrutin'].split('-')))

    @property
    def synthese(self):
        synthese = self.scrutin['syntheseVote']
        decompte = synthese['decompte']
        return f"{synthese['nombreVotants']} votants, " \
               f"{decompte['pour']} pour, " \
               f"{decompte['contre']} contre, " \
               f"{decompte['abstentions']} abstentions"

    def send(self, postman: TweetPostman, medias=None):
        postman.post_tweet(
            text=self.__str__(),
            medias=medias
        )
