import numpy as np
import pandas as pd
DAYS=36
WINDOWS=[3,7,14,30,36]
def _cols(v,n): return [f"{v}{i}" for i in range(n)]
def engineer_features(df):
 df=df.copy(); p=_cols("precip",DAYS)
 df["rain_1d"]=df["precip0"]
 for n in (3,7,30): df[f"rain_{n}d"]=df[_cols("precip",n)].sum(axis=1)
 df["rain_35d"]=df[p].sum(axis=1); df["rain_mean_35d"]=df[p].mean(axis=1); df["rain_max_35d"]=df[p].max(axis=1); df["rain_std_35d"]=df[p].std(axis=1); df["rain_min_35d"]=df[p].min(axis=1)
 for w in (3,7,14,30):
  b=df[_cols("precip",w)]; df[f"rain_max_{w}d"]=b.max(axis=1); df[f"rain_mean_{w}d"]=b.mean(axis=1); df[f"rain_std_{w}d"]=b.std(axis=1)
 for w in WINDOWS: df[f"wet_days_{w}d"]=(df[_cols("precip",w)]>5).sum(axis=1)
 for w in (7,14,30): df[f"heavy_rain_days_{w}d"]=(df[_cols("precip",w)]>20).sum(axis=1)
 df["recent_rain_7d"]=df[_cols("precip",7)].sum(axis=1); df["previous_rain_7d"]=df[[f"precip{i}" for i in range(7,14)]].sum(axis=1); df["rain_trend_7d"]=df["recent_rain_7d"]-df["previous_rain_7d"]; df["rain_ratio_7d"]=df["recent_rain_7d"]/(df["previous_rain_7d"]+1e-6)
 w=np.exp(-np.arange(DAYS)/7); w=w/w.sum(); df["antecedent_rainfall_index"]=df[p].fillna(0).values@w
 stats={"temp":("mean","max","min","std"),"humidity":("mean","max","min","std"),"wind":("mean","max","std"),"air":("mean","max","min","std")}
 for var,ss in stats.items():
  for ww in WINDOWS:
   b=df[_cols(var,ww)]
   for s in ss: df[f"{var}_{s}_{ww}d"]=getattr(b,s)(axis=1)
 df["slope_squared"]=df["slope"]**2
 return df.drop(columns=["date"],errors="ignore")
