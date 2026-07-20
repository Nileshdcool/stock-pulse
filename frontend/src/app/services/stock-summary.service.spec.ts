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

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/stocks/AAPL/summary`);
    expect(req.request.method).toBe('GET');
    req.flush({
      symbol: 'AAPL',
      summary: 'Test summary',
      bullets: ['One'],
      sources: [],
      generated_at: '2024-01-01T00:00:00Z',
      cached: false,
    });
  });

  it('maps API detail into an error message', (done) => {
    service.getSummary('AAPL').subscribe({
      next: () => done.fail('expected error'),
      error: (message: string) => {
        expect(message).toBe('No recent news found for AAPL');
        done();
      },
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/stocks/AAPL/summary`);
    req.flush({ detail: 'No recent news found for AAPL' }, { status: 404, statusText: 'Not Found' });
  });
});
