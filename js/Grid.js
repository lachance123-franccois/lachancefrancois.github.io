/* Grille et utilitaires minimaux : remplacent Bootstrap sur les pages qui ne le chargent plus.
   Les noms de classes et de variables sont ceux de Bootstrap, pour ne rien changer au HTML. */
.row {
  --bs-gutter-x: 1.5rem; --bs-gutter-y: 0;
  display: flex; flex-wrap: wrap;
  margin-top: calc(-1 * var(--bs-gutter-y));
  margin-inline: calc(-.5 * var(--bs-gutter-x));
}
.row > * {
  flex-shrink: 0; width: 100%; max-width: 100%;
  padding-inline: calc(var(--bs-gutter-x) * .5);
  margin-top: var(--bs-gutter-y);
}
.g-4 { --bs-gutter-x: 1.5rem; --bs-gutter-y: 1.5rem; }
.g-5 { --bs-gutter-x: 3rem;   --bs-gutter-y: 3rem; }

@media (min-width: 768px) {
  .col-md-4 { flex: 0 0 auto; width: 33.33333%; }
  .col-md-6 { flex: 0 0 auto; width: 50%; }
}
@media (min-width: 992px) {
  .col-lg-3 { flex: 0 0 auto; width: 25%; }
  .col-lg-4 { flex: 0 0 auto; width: 33.33333%; }
  .col-lg-5 { flex: 0 0 auto; width: 41.66667%; }
  .col-lg-6 { flex: 0 0 auto; width: 50%; }
  .col-lg-7 { flex: 0 0 auto; width: 58.33333%; }
  .order-lg-1 { order: 1 !important; }
  .order-lg-2 { order: 2 !important; }
}
.order-1 { order: 1; }
.order-2 { order: 2; }
.align-items-center { align-items: center; }
.mt-4 { margin-top: 1.5rem !important; }
.mb-0 { margin-bottom: 0 !important; }
.text-muted { color: var(--text-muted) !important; }