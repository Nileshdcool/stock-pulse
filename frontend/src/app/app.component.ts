import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { StockSummaryService } from './services/stock-summary.service';
import { NewsPeriod, SummaryResponse } from './models/summary';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private readonly stockSummary = inject(StockSummaryService);

  readonly suggestions = ['AAPL', 'MSFT', 'TSLA', 'NVDA'] as const;

  readonly periodOptions: ReadonlyArray<{ value: NewsPeriod; label: string }> = [
    { value: '1d', label: '1 day' },
    { value: '7d', label: '7 days' },
    { value: '30d', label: '30 days' },
  ];

  readonly symbolControl = new FormControl('AAPL', {
    nonNullable: true,
    validators: [Validators.required, Validators.pattern(/^[A-Za-z0-9.-]{1,12}$/)],
  });

  readonly periodControl = new FormControl<NewsPeriod>('7d', { nonNullable: true });

  loading = false;
  error: string | null = null;
  result: SummaryResponse | null = null;
  logoFailed = false;

  onSymbolInput(): void {
    const value = this.symbolControl.value;
    const upper = value.toUpperCase();
    if (value !== upper) {
      this.symbolControl.setValue(upper, { emitEvent: false });
    }
  }

  selectPeriod(period: NewsPeriod): void {
    if (this.periodControl.value === period) {
      return;
    }
    this.periodControl.setValue(period);
    if (this.symbolControl.valid && (this.result || this.error)) {
      this.submit();
    }
  }

  useSuggestion(symbol: string): void {
    this.symbolControl.setValue(symbol);
    this.symbolControl.markAsTouched();
    this.submit();
  }

  onLogoError(): void {
    this.logoFailed = true;
  }

  formatPeriod(period: NewsPeriod): string {
    switch (period) {
      case '1d':
        return 'Last 24 hours';
      case '7d':
        return 'Last 7 days';
      case '30d':
        return 'Last 30 days';
    }
  }

  formatGeneratedAt(iso: string): string {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) {
      return '';
    }
    return `Updated ${date.toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })}`;
  }

  formatPublishedAt(iso: string): string {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) {
      return '';
    }
    return date.toLocaleDateString(undefined, { dateStyle: 'medium' });
  }

  tickersFor(source: { related_symbols?: string[] | null }): string[] {
    const related = source.related_symbols?.filter(Boolean) ?? [];
    if (related.length) {
      return related;
    }
    return this.result?.symbol ? [this.result.symbol] : [];
  }

  onFormSubmit(event: Event): void {
    event.preventDefault();
    this.submit();
  }

  submit(): void {
    if (this.symbolControl.invalid) {
      this.symbolControl.markAsTouched();
      return;
    }

    this.loading = true;
    this.error = null;
    this.result = null;
    this.logoFailed = false;

    this.stockSummary.getSummary(this.symbolControl.value, this.periodControl.value).subscribe({
      next: (response) => {
        this.result = response;
        this.loading = false;
      },
      error: (message: string) => {
        this.error = message;
        this.loading = false;
      },
    });
  }
}
