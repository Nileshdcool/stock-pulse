import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { AppComponent } from './app.component';
import { StockSummaryService } from './services/stock-summary.service';
import { SummaryResponse } from './models/summary';

describe('AppComponent', () => {
  let fixture: ComponentFixture<AppComponent>;
  let component: AppComponent;
  let stockSummary: { getSummary: jest.Mock };

  const sample: SummaryResponse = {
    symbol: 'AAPL',
    company_name: 'Apple Inc',
    logo_url: 'https://example.com/aapl.png',
    summary: 'Apple news looks constructive.',
    bullets: ['iPhone sales strong'],
    sources: [
      {
        title: 'Apple reports strong iPhone sales',
        url: 'https://example.com/news/1',
        source: 'Reuters',
        published_at: '2024-06-01T00:00:00Z',
        related_symbols: ['AAPL'],
      },
    ],
    period: '7d',
    generated_at: '2024-06-01T00:00:00Z',
    cached: false,
  };

  beforeEach(async () => {
    stockSummary = {
      getSummary: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideNoopAnimations(),
        { provide: StockSummaryService, useValue: stockSummary },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('shows loading then summary on success', () => {
    stockSummary.getSummary.mockReturnValue(of(sample));
    component.submit();
    fixture.detectChanges();

    expect(component.loading).toBe(false);
    expect(component.result?.summary).toBe('Apple news looks constructive.');
    expect(fixture.nativeElement.textContent).toContain('Apple news looks constructive.');
    expect(fixture.nativeElement.textContent).toContain('Apple reports strong iPhone sales');
    expect(fixture.nativeElement.querySelector('.identity-title h2')?.textContent).toContain('AAPL');
    expect(fixture.nativeElement.querySelector('.company-name')?.textContent).toContain('Apple Inc');
    expect(fixture.nativeElement.querySelector('.company-logo')?.getAttribute('src')).toBe(
      'https://example.com/aapl.png',
    );
    expect(fixture.nativeElement.querySelector('.ticker-chip')?.textContent).toContain('AAPL');
  });

  it('shows an error message when the service fails', () => {
    stockSummary.getSummary.mockReturnValue(throwError(() => 'Backend unavailable'));
    component.submit();
    fixture.detectChanges();

    expect(component.error).toBe('Backend unavailable');
    expect(fixture.nativeElement.textContent).toContain('Backend unavailable');
  });

  it('loads a summary when a suggestion is clicked', () => {
    stockSummary.getSummary.mockReturnValue(of(sample));
    component.useSuggestion('MSFT');
    fixture.detectChanges();

    expect(component.symbolControl.value).toBe('MSFT');
    expect(stockSummary.getSummary).toHaveBeenCalledWith('MSFT', '7d');
  });

  it('loads a summary when the form is submitted', () => {
    stockSummary.getSummary.mockReturnValue(of(sample));
    const event = { preventDefault: jest.fn() } as unknown as Event;

    component.onFormSubmit(event);
    fixture.detectChanges();

    expect(event.preventDefault).toHaveBeenCalled();
    expect(stockSummary.getSummary).toHaveBeenCalledWith('AAPL', '7d');
    expect(component.result?.summary).toBe('Apple news looks constructive.');
  });

  it('refetches when the period changes after a result', () => {
    stockSummary.getSummary.mockReturnValue(of({ ...sample, period: '30d' }));
    component.result = sample;
    component.selectPeriod('30d');
    fixture.detectChanges();

    expect(component.periodControl.value).toBe('30d');
    expect(stockSummary.getSummary).toHaveBeenCalledWith('AAPL', '30d');
  });

  it('uppercases ticker input as the user types', () => {
    component.symbolControl.setValue('tsla');
    component.onSymbolInput();
    expect(component.symbolControl.value).toBe('TSLA');
  });
});
