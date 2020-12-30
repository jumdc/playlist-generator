import config
import spotipy
import datetime
import numpy as np
from random import shuffle
import spotipy.util as util
import matplotlib.pyplot as plt
from spotipy.oauth2 import SpotifyClientCredentials

class Recommendation():
    def __init__(self,username,cid,secret,redirect_uri,uri_playlist,id_playlist):
        """
        redirect_uri : the same than in the app details on the SpotifyDev 
        """
        
        scope='user-top-read user-read-recently-played playlist-modify-private user-library-modify playlist-modify-public playlist-read-collaborative ugc-image-upload'
        token = util.prompt_for_user_token(username=username, 
                                        scope=scope, 
                                        client_id=cid,   
                                        client_secret=secret,     
                                        redirect_uri=redirect_uri)
        self.sp=spotipy.Spotify(auth=token)
        self.uri_playlist=uri_playlist
        self.id_playlist=id_playlist
        self.username=username

    def get_reco(self,artistSeeds,genres,trackSeeds):
        dataReco=self.sp.recommendations(seed_artists=artistSeeds,seed_genres=genres,seed_tracks=trackSeeds)
        listReco=[]
        for i in range(len(dataReco['tracks'])):
            if dataReco['tracks'][i]['artists'][0]['uri'] not in artistSeeds:
                listReco.append(dataReco['tracks'][i]['uri'])      
        return listReco
    
    def get_top_songs(self):
        """Finds your current top songs"""
        data = self.sp.current_user_top_tracks(time_range='short_term')
        top=[]
        for song in data['items']:
            top.append((song['uri'],song['name'],song['artists'][0]['name']))
        return top 
    
    def get_top_artists_genres(self):
        """Finds your top artists and associated genres"""
        data2 = self.sp.current_user_top_artists(time_range='short_term')
        topA=[]
        genres=[]
        genresArt=[]
        occurences=[]
        genreA=[]
        for art in data2['items']:
            topA.append((art['uri'],art['name']))
            tamp=art['genres']
            for i in tamp:
                if i not in genresArt:
                    genresArt.append(i)
                    occurences.append(1)
                else: 
                    indice=genresArt.index(i)
                    occurences[indice]+=1
        genreA=list(zip(genresArt,occurences))            
        genreA.sort(key=lambda x:x[1],reverse=True)
        for i in range(5):
            genres.append(genreA[i][0])
        return topA,genres
    
    def seeds(self,top_tracks,top_artists):
        """
        gets the seeds of tracks & artists
        
        params : 
        top_tracks : list of top tracks
        top_artists : list of top_artists
        """ 
        artistSeeds=[]
        trackSeeds=[]
        for comp in range(7):
            artistSeeds.append(top_artists[comp][0])
            trackSeeds.append(top_tracks[comp][0])
        return trackSeeds,artistSeeds
    
    def update_playlist(self,list_recommendation):
        """
        Updates the playlist
        
        remove the current tracks and then updates its content & title
        """
        date=datetime.datetime.now()
        nameP=str(date)[:19]
        
        get_tracks=self.sp.user_playlist_tracks(user=self.username,playlist_id=self.uri_playlist)
        all_tracks=[]
        for track in get_tracks['items']:
            all_tracks.append(track['track']['uri'])
        self.sp.user_playlist_remove_all_occurrences_of_tracks(user=self.username,playlist_id=self.uri_playlist,tracks=all_tracks)
        self.sp.user_playlist_change_details(user=self.username,playlist_id=self.id_playlist,name=nameP)
        self.sp.user_playlist_add_tracks(user=self.username,playlist_id=self.uri_playlist,tracks=listReco)

           
    def getFeaturesMean(self,tracks):
        """
        Returns the mean of the features of the tracks
        
        params:
        tracks: list of tracks 
        """
        tempo,dance,loudness,valence,energy,instrumentalness,acousticness,key,speechiness,duration_ms=[],[],[],[],[],[],[],[],[],[]
        for uri in tracks:
            res=self.sp.audio_features(uri)
            tempo.append(res[0]['tempo'])
            dance.append(res[0]['danceability'])
            loudness.append(res[0]['loudness'])
            valence.append(res[0]['valence'])
            energy.append(res[0]['energy'])
            instrumentalness.append(res[0]['instrumentalness'])
            acousticness.append(res[0]['acousticness'])
            key.append(res[0]['key'])
            speechiness.append(res[0]['speechiness']*100)
            duration_ms.append(res[0]['duration_ms'])
        
        meanTempo=int(sum(tempo)/len(tempo))
        meanDance=int(sum(dance)/len(dance)*100)
        meanLoudness=sum(loudness)/len(loudness)
        meanValence=int(sum(valence)/len(valence)*100)
        meanEnergy=int(sum(energy)/len(energy)*100)
        meanInstrumental=int(sum(instrumentalness)/len(instrumentalness)*100)
        meanAcousticness=int(sum(acousticness)/len(acousticness)*100)
        meanSpeech=sum(speechiness)/len(speechiness)
        return meanTempo,meanDance,meanLoudness,meanValence,meanEnergy,meanInstrumental,meanAcousticness,meanSpeech


if __name__ == "__main__":
    username = config.username
    cid = config.cid
    secret = config.secret
    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    redirect_uri = config.redirect_uri
    uri_playlist=config.uriPlaylist
    id_playlist=config.idPlaylist
    
    reco=Recommendation(username,cid,secret,redirect_uri,uri_playlist,id_playlist)

    top_artists,top_genres=reco.get_top_artists_genres()
    top_tracks=reco.get_top_songs()
    t_seeds,a_seeds=reco.seeds(top_tracks,top_artists)
    

    listReco1=reco.get_reco(a_seeds[:2],top_genres[:1],t_seeds[:2])
    listReco2=reco.get_reco(a_seeds[2:4],top_genres[1:2],t_seeds[2:4])
    listReco3=reco.get_reco(a_seeds[4:6],top_genres[2:3],t_seeds[4:6])
    listReco=listReco1+listReco2+listReco3
    shuffle(listReco)
    
    reco.update_playlist(listReco)
    
    meanTempo,meanDance,meanLoudness,meanValence,meanEnergy,meanInstrumental,meanAcousticness,meanSpeech=reco.getFeaturesMean(listReco)
    title='Info Playlist, tempo moyen:'+str(meanTempo)
    plt.title(title)
    data=[meanAcousticness,meanDance,meanEnergy,meanInstrumental,meanLoudness,meanSpeech,meanValence]
    features=('Acousticness','danceability','energy','instrumentalness','loudness','speechiness','valence')
    y_pos=np.arange(len(data))
    plt.bar(y_pos,data,color=['gold','violet','blue','orange','green','hotpink','slategrey'])
    plt.xticks(y_pos,features)
    plt.show()

    print("** Bases de la Recommendantion: **")
    print()
    print('- Artists:')
    print(top_artists[0][1],top_artists[1][1],top_artists[2][1],top_artists[3][1],top_artists[4][1])
    print('- Tracks:')
    print(top_tracks[0][1],top_tracks[1][1],top_tracks[2][1],top_tracks[3][1],top_tracks[4][1])
    print('- Genres')
    print(top_genres[0],top_genres[1],top_genres[2])

