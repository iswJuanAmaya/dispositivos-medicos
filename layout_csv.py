
import pandas as pd

#crea el layout del csv de oportunidades
df = pd.DataFrame(columns=['url_detail_id','scrapped_day','title','opening_date',
                           'closing_date','source','is_alert','location','tipo','reference','organization'])

df.to_csv('oportunidades.csv', index=False, encoding='utf-8', header=True)