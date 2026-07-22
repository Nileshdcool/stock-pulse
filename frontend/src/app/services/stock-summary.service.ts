import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { NewsPeriod, SummaryResponse } from '../models/summary';

@Injectable({ providedIn: 'root' })
export class StockSummaryService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getSummary(symbol: string, period: NewsPeriod = '7d'): Observable<SummaryResponse> {
    const trimmed = symbol.trim().toUpperCase();
    const params = new HttpParams().set('period', period);
    return this.http
      .get<SummaryResponse>(`${this.baseUrl}/api/stocks/${encodeURIComponent(trimmed)}/summary`, {
        params,
      })
      .pipe(catchError((error: HttpErrorResponse) => throwError(() => this.toMessage(error))));
  }

  private toMessage(error: HttpErrorResponse): string {
    if (typeof error.error?.detail === 'string') {
      return error.error.detail;
    }
    if (error.status === 0) {
      return 'Cannot reach the API. Is the backend running on port 8000?';
    }
    return error.message || 'Unexpected error while loading the summary.';
  }
}
