import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { StockSummaryService } from './stock-summary.service';
import { environment } from '../../environments/environment';

describe('StockSummaryService', () => {
  let service: StockSummaryService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
    });
    service = TestBed.inject(StockSummaryService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('requests summary for an uppercased symbol', () => {
    service.getSummary('aapl').subscribe((result) => {
      expect(result.symbol).toBe('AAPL');
    });

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/api/stocks/AAPL/summary?period=7d`,
    );
    expect(req.request.method).toBe('GET');
    req.flush({
      symbol: 'AAPL',
      summary: 'Test summary',
      bullets: ['One'],
      sources: [],
      period: '7d',
      generated_at: '2024-01-01T00:00:00Z',
      cached: false,
    });
  });

  it('passes the selected period as a query param', () => {
    service.getSummary('MSFT', '30d').subscribe();

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/api/stocks/MSFT/summary?period=30d`,
    );
    expect(req.request.params.get('period')).toBe('30d');
    req.flush({
      symbol: 'MSFT',
      summary: 'Test summary',
      bullets: ['One'],
      sources: [],
      period: '30d',
      generated_at: '2024-01-01T00:00:00Z',
      cached: false,
    });
  });

  it('maps API detail into an error message', (done) => {
    service.getSummary('AAPL').subscribe({
      next: () => done.fail('expected error'),
      error: (message: string) => {
        expect(message).toBe('No news found for AAPL in the last 7d. Try a longer period or another symbol.');
        done();
      },
    });

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/api/stocks/AAPL/summary?period=7d`,
    );
    req.flush(
      {
        detail:
          'No news found for AAPL in the last 7d. Try a longer period or another symbol.',
      },
      { status: 404, statusText: 'Not Found' },
    );
  });
});
