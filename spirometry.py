
import pandas as pd
import os

def flow_volume(path, timecol, volumecol, flowcol):
    """
    fed each file name from the index_directory function and creates a data frame of
    that MEFV curve
    """
    df = pd.read_csv(path, delimiter='\t')
    flow = pd.Series(df.iloc[:, (flowcol)], name='flow')
    volume = pd.Series(df.iloc[:, (volumecol)], name='volume')
    df = pd.concat([flow, volume], axis=1)
    total_lung_capacity = df['volume'][0]
    df['volume'] = (df['volume'] - total_lung_capacity).round(2)
    df = df.groupby('volume').mean()
    return df

def index_directory(path, timecol, volumecol, flowcol):
    """
    Indexes the folder with FVC files and combines into one master 
    df by adding each to the bottom
    """
    master_df = pd.DataFrame()
    dl = os.listdir(path)
    for f in dl:
        if f.endswith(".txt"):
            path_in = os.path.join(path,f)
            df = flow_volume(path_in, timecol,  volumecol, flowcol)
            master_df = pd.concat([master_df, df])
    
    return master_df

def mefv_curve(path, timecol, volumecol, flowcol):
    """
    creates final mefv curve by taking master mefv dataframe and taking highest flow at
    every lung volume 
    """
    mefv = index_directory(path, timecol, volumecol, flowcol)
    mefv = mefv.groupby('volume').max().reset_index()
    mefv = mefv[mefv['volume'] >= 0]
    mefv.volume = mefv.volume.values[::-1]
    return mefv

def get_fvc(mefv):
    vital_capacity = mefv['volume'].iloc[0]
    return vital_capacity

def get_peak_flow(mefv):
    peak_flow = mefv['flow'].max()
    return peak_flow

def get_fev1(mefv):
    mefv.volume = mefv.volume.values[::-1]
    mefv['time'] = (0.01 / mefv['flow']).cumsum().round(2)
    fev1 = mefv.loc[mefv['time'] == 1.00, 'volume'].iloc[0]
    
    return fev1

def get_mid_flows(mefv):
    mefv['percent'] = (mefv.volume / float(mefv.volume.iat[-1])).round(2)

    fef25 = mefv.loc[mefv['percent'] == 0.25, 'flow'].iloc[0].round(2)
    fef50 = mefv.loc[mefv['percent'] == 0.50, 'flow'].iloc[0].round(2)
    fef75 = mefv.loc[mefv['percent'] == 0.75, 'flow'].iloc[0].round(2)

    return fef25, fef50, fef75

def get_slope_ratio(mefv):
    mefv_sr = mefv.copy()
    mefv_sr['percent'] = mefv_sr.volume / mefv_sr.volume.max()
    mefv_sr['volume'] = mefv_sr['volume'].values[::-1]
    count = 0
    sr_sum = 0
    for i in range(len(mefv_sr)-1):
        point = mefv_sr['percent'].iloc[i]
        if 0.20 <= point <= 0.80:
            flow_above = mefv_sr.loc[mefv_sr['volume'] == (round(mefv_sr['volume'][i]+0.2, 2)), 'flow'].values[0]
            flow_below = mefv_sr.loc[mefv_sr['volume'] == (round(mefv_sr['volume'][i]-0.2, 2)), 'flow'].values[0]
            tan = (flow_below - flow_above) / 0.4
            chord = mefv_sr['flow'][i] / mefv_sr['volume'][i]
            sr = abs(tan / chord)
            sr_sum += sr
            count += 1
    slope_ratio = sr_sum / count
    return(slope_ratio)