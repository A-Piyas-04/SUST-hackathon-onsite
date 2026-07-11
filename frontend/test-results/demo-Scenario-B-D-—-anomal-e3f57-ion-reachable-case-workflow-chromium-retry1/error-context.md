# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: demo.spec.ts >> Scenario B & D — anomaly evidence, localized explanation, reachable case workflow
- Location: e2e\demo.spec.ts:52:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Explanation')
Expected: visible
Error: strict mode violation: getByText('Explanation') resolved to 2 elements:
    1) <p class="text-xs text-zinc-500">Published, evidence-backed alerts. Select one to …</p> aka getByText('Published, evidence-backed')
    2) <h3 class="text-sm font-semibold">Explanation</h3> aka getByRole('heading', { name: 'Explanation' })

Call log:
  - Expect "toBeVisible" with timeout 20000ms
  - waiting for getByText('Explanation')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - button "Open Next.js Dev Tools" [ref=e7] [cursor=pointer]:
    - img [ref=e8]
  - alert [ref=e11]
  - generic [ref=e12]:
    - banner [ref=e13]:
      - generic [ref=e14]:
        - generic [ref=e15]:
          - paragraph [ref=e16]: Liquidity & Coordination Platform
          - paragraph [ref=e17]: Decision-support demo · http://localhost:8000
        - generic [ref=e18]:
          - generic [ref=e19]:
            - paragraph [ref=e20]: Demo Risk Analyst (bKash)
            - paragraph [ref=e21]:
              - generic [ref=e22]: risk_analyst
              - text: provider-scoped
          - generic [ref=e23]:
            - button "English" [ref=e24]
            - button "বাংলা" [ref=e25]
            - button "Banglish" [ref=e26]
          - button "Log out" [ref=e27]
      - navigation [ref=e28]:
        - button "Dashboard" [ref=e29]
        - button "Liquidity" [ref=e30]
        - button "Anomalies" [ref=e31]
        - button "Scenarios & Faults" [ref=e32]
        - button "Alerts" [ref=e33]
        - button "Cases" [ref=e34]
        - button "Notifications" [ref=e35]
    - main [ref=e36]:
      - generic [ref=e37]:
        - generic [ref=e38]: Outlet
        - combobox [ref=e39]:
          - option "OUTLET-001 — Demo Outlet 001 (Market)" [selected]
          - option "OUTLET-002 — Demo Outlet 002 (Riverside)"
      - generic [ref=e40]:
        - generic [ref=e41]:
          - heading "Alerts" [level=2] [ref=e42]
          - paragraph [ref=e43]: Published, evidence-backed alerts. Select one to read its explanation in English, বাংলা, or Banglish.
        - generic [ref=e44]:
          - list [ref=e46]:
            - listitem [ref=e47]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:58" [active] [ref=e48]:
                - generic [ref=e49]:
                  - generic [ref=e50]: Unusual activity — requires review
                  - generic [ref=e51]: high
                - paragraph [ref=e52]: anomaly · 11 Jul 2026, 19:58
            - listitem [ref=e53]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:58" [ref=e54]:
                - generic [ref=e55]:
                  - generic [ref=e56]: alert liquidity shortage
                  - generic [ref=e57]: medium
                - paragraph [ref=e58]: liquidity · 11 Jul 2026, 19:58
            - listitem [ref=e59]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:58" [ref=e60]:
                - generic [ref=e61]:
                  - generic [ref=e62]: Unusual activity — requires review
                  - generic [ref=e63]: high
                - paragraph [ref=e64]: anomaly · 11 Jul 2026, 19:58
            - listitem [ref=e65]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:58" [ref=e66]:
                - generic [ref=e67]:
                  - generic [ref=e68]: alert liquidity shortage
                  - generic [ref=e69]: medium
                - paragraph [ref=e70]: liquidity · 11 Jul 2026, 19:58
            - listitem [ref=e71]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:43" [ref=e72]:
                - generic [ref=e73]:
                  - generic [ref=e74]: Unusual activity — requires review
                  - generic [ref=e75]: high
                - paragraph [ref=e76]: anomaly · 11 Jul 2026, 19:43
            - listitem [ref=e77]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:43" [ref=e78]:
                - generic [ref=e79]:
                  - generic [ref=e80]: alert liquidity shortage
                  - generic [ref=e81]: medium
                - paragraph [ref=e82]: liquidity · 11 Jul 2026, 19:43
            - listitem [ref=e83]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e84]:
                - generic [ref=e85]:
                  - generic [ref=e86]: Unusual activity — requires review
                  - generic [ref=e87]: high
                - paragraph [ref=e88]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e89]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e90]:
                - generic [ref=e91]:
                  - generic [ref=e92]: alert liquidity shortage
                  - generic [ref=e93]: medium
                - paragraph [ref=e94]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e95]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e96]:
                - generic [ref=e97]:
                  - generic [ref=e98]: Unusual activity — requires review
                  - generic [ref=e99]: high
                - paragraph [ref=e100]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e101]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e102]:
                - generic [ref=e103]:
                  - generic [ref=e104]: alert liquidity shortage
                  - generic [ref=e105]: medium
                - paragraph [ref=e106]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e107]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e108]:
                - generic [ref=e109]:
                  - generic [ref=e110]: Unusual activity — requires review
                  - generic [ref=e111]: high
                - paragraph [ref=e112]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e113]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e114]:
                - generic [ref=e115]:
                  - generic [ref=e116]: alert liquidity shortage
                  - generic [ref=e117]: medium
                - paragraph [ref=e118]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e119]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e120]:
                - generic [ref=e121]:
                  - generic [ref=e122]: Unusual activity — requires review
                  - generic [ref=e123]: high
                - paragraph [ref=e124]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e125]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e126]:
                - generic [ref=e127]:
                  - generic [ref=e128]: alert liquidity shortage
                  - generic [ref=e129]: medium
                - paragraph [ref=e130]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e131]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e132]:
                - generic [ref=e133]:
                  - generic [ref=e134]: Unusual activity — requires review
                  - generic [ref=e135]: high
                - paragraph [ref=e136]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e137]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e138]:
                - generic [ref=e139]:
                  - generic [ref=e140]: alert liquidity shortage
                  - generic [ref=e141]: medium
                - paragraph [ref=e142]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e143]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e144]:
                - generic [ref=e145]:
                  - generic [ref=e146]: Unusual activity — requires review
                  - generic [ref=e147]: high
                - paragraph [ref=e148]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e149]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e150]:
                - generic [ref=e151]:
                  - generic [ref=e152]: alert liquidity shortage
                  - generic [ref=e153]: medium
                - paragraph [ref=e154]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e155]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e156]:
                - generic [ref=e157]:
                  - generic [ref=e158]: Unusual activity — requires review
                  - generic [ref=e159]: high
                - paragraph [ref=e160]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e161]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e162]:
                - generic [ref=e163]:
                  - generic [ref=e164]: alert liquidity shortage
                  - generic [ref=e165]: medium
                - paragraph [ref=e166]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e167]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e168]:
                - generic [ref=e169]:
                  - generic [ref=e170]: Unusual activity — requires review
                  - generic [ref=e171]: high
                - paragraph [ref=e172]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e173]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e174]:
                - generic [ref=e175]:
                  - generic [ref=e176]: alert liquidity shortage
                  - generic [ref=e177]: medium
                - paragraph [ref=e178]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e179]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e180]:
                - generic [ref=e181]:
                  - generic [ref=e182]: Unusual activity — requires review
                  - generic [ref=e183]: high
                - paragraph [ref=e184]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e185]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e186]:
                - generic [ref=e187]:
                  - generic [ref=e188]: alert liquidity shortage
                  - generic [ref=e189]: medium
                - paragraph [ref=e190]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e191]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e192]:
                - generic [ref=e193]:
                  - generic [ref=e194]: Unusual activity — requires review
                  - generic [ref=e195]: high
                - paragraph [ref=e196]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e197]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e198]:
                - generic [ref=e199]:
                  - generic [ref=e200]: alert liquidity shortage
                  - generic [ref=e201]: medium
                - paragraph [ref=e202]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e203]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e204]:
                - generic [ref=e205]:
                  - generic [ref=e206]: Unusual activity — requires review
                  - generic [ref=e207]: high
                - paragraph [ref=e208]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e209]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e210]:
                - generic [ref=e211]:
                  - generic [ref=e212]: alert liquidity shortage
                  - generic [ref=e213]: medium
                - paragraph [ref=e214]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e215]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e216]:
                - generic [ref=e217]:
                  - generic [ref=e218]: Unusual activity — requires review
                  - generic [ref=e219]: high
                - paragraph [ref=e220]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e221]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e222]:
                - generic [ref=e223]:
                  - generic [ref=e224]: alert liquidity shortage
                  - generic [ref=e225]: medium
                - paragraph [ref=e226]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e227]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e228]:
                - generic [ref=e229]:
                  - generic [ref=e230]: Unusual activity — requires review
                  - generic [ref=e231]: high
                - paragraph [ref=e232]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e233]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e234]:
                - generic [ref=e235]:
                  - generic [ref=e236]: alert liquidity shortage
                  - generic [ref=e237]: medium
                - paragraph [ref=e238]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e239]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e240]:
                - generic [ref=e241]:
                  - generic [ref=e242]: Unusual activity — requires review
                  - generic [ref=e243]: high
                - paragraph [ref=e244]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e245]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e246]:
                - generic [ref=e247]:
                  - generic [ref=e248]: alert liquidity shortage
                  - generic [ref=e249]: medium
                - paragraph [ref=e250]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e251]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e252]:
                - generic [ref=e253]:
                  - generic [ref=e254]: Unusual activity — requires review
                  - generic [ref=e255]: high
                - paragraph [ref=e256]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e257]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e258]:
                - generic [ref=e259]:
                  - generic [ref=e260]: alert liquidity shortage
                  - generic [ref=e261]: medium
                - paragraph [ref=e262]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e263]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e264]:
                - generic [ref=e265]:
                  - generic [ref=e266]: Unusual activity — requires review
                  - generic [ref=e267]: high
                - paragraph [ref=e268]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e269]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e270]:
                - generic [ref=e271]:
                  - generic [ref=e272]: alert liquidity shortage
                  - generic [ref=e273]: medium
                - paragraph [ref=e274]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e275]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e276]:
                - generic [ref=e277]:
                  - generic [ref=e278]: Unusual activity — requires review
                  - generic [ref=e279]: high
                - paragraph [ref=e280]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e281]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e282]:
                - generic [ref=e283]:
                  - generic [ref=e284]: alert liquidity shortage
                  - generic [ref=e285]: medium
                - paragraph [ref=e286]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e287]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e288]:
                - generic [ref=e289]:
                  - generic [ref=e290]: Unusual activity — requires review
                  - generic [ref=e291]: high
                - paragraph [ref=e292]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e293]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e294]:
                - generic [ref=e295]:
                  - generic [ref=e296]: alert liquidity shortage
                  - generic [ref=e297]: medium
                - paragraph [ref=e298]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e299]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e300]:
                - generic [ref=e301]:
                  - generic [ref=e302]: Unusual activity — requires review
                  - generic [ref=e303]: high
                - paragraph [ref=e304]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e305]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e306]:
                - generic [ref=e307]:
                  - generic [ref=e308]: alert liquidity shortage
                  - generic [ref=e309]: medium
                - paragraph [ref=e310]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e311]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e312]:
                - generic [ref=e313]:
                  - generic [ref=e314]: Unusual activity — requires review
                  - generic [ref=e315]: high
                - paragraph [ref=e316]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e317]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e318]:
                - generic [ref=e319]:
                  - generic [ref=e320]: alert liquidity shortage
                  - generic [ref=e321]: medium
                - paragraph [ref=e322]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e323]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e324]:
                - generic [ref=e325]:
                  - generic [ref=e326]: Unusual activity — requires review
                  - generic [ref=e327]: high
                - paragraph [ref=e328]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e329]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e330]:
                - generic [ref=e331]:
                  - generic [ref=e332]: alert liquidity shortage
                  - generic [ref=e333]: medium
                - paragraph [ref=e334]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e335]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e336]:
                - generic [ref=e337]:
                  - generic [ref=e338]: alert liquidity shortage
                  - generic [ref=e339]: medium
                - paragraph [ref=e340]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e341]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e342]:
                - generic [ref=e343]:
                  - generic [ref=e344]: Unusual activity — requires review
                  - generic [ref=e345]: high
                - paragraph [ref=e346]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e347]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e348]:
                - generic [ref=e349]:
                  - generic [ref=e350]: alert liquidity shortage
                  - generic [ref=e351]: medium
                - paragraph [ref=e352]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e353]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e354]:
                - generic [ref=e355]:
                  - generic [ref=e356]: Unusual activity — requires review
                  - generic [ref=e357]: high
                - paragraph [ref=e358]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e359]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e360]:
                - generic [ref=e361]:
                  - generic [ref=e362]: alert liquidity shortage
                  - generic [ref=e363]: medium
                - paragraph [ref=e364]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e365]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e366]:
                - generic [ref=e367]:
                  - generic [ref=e368]: Unusual activity — requires review
                  - generic [ref=e369]: high
                - paragraph [ref=e370]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e371]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e372]:
                - generic [ref=e373]:
                  - generic [ref=e374]: alert liquidity shortage
                  - generic [ref=e375]: medium
                - paragraph [ref=e376]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e377]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e378]:
                - generic [ref=e379]:
                  - generic [ref=e380]: Unusual activity — requires review
                  - generic [ref=e381]: high
                - paragraph [ref=e382]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e383]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e384]:
                - generic [ref=e385]:
                  - generic [ref=e386]: alert liquidity shortage
                  - generic [ref=e387]: medium
                - paragraph [ref=e388]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e389]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e390]:
                - generic [ref=e391]:
                  - generic [ref=e392]: Unusual activity — requires review
                  - generic [ref=e393]: high
                - paragraph [ref=e394]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e395]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e396]:
                - generic [ref=e397]:
                  - generic [ref=e398]: alert liquidity shortage
                  - generic [ref=e399]: medium
                - paragraph [ref=e400]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e401]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e402]:
                - generic [ref=e403]:
                  - generic [ref=e404]: Unusual activity — requires review
                  - generic [ref=e405]: high
                - paragraph [ref=e406]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e407]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e408]:
                - generic [ref=e409]:
                  - generic [ref=e410]: alert liquidity shortage
                  - generic [ref=e411]: medium
                - paragraph [ref=e412]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e413]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e414]:
                - generic [ref=e415]:
                  - generic [ref=e416]: Unusual activity — requires review
                  - generic [ref=e417]: high
                - paragraph [ref=e418]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e419]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e420]:
                - generic [ref=e421]:
                  - generic [ref=e422]: alert liquidity shortage
                  - generic [ref=e423]: medium
                - paragraph [ref=e424]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e425]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e426]:
                - generic [ref=e427]:
                  - generic [ref=e428]: Unusual activity — requires review
                  - generic [ref=e429]: high
                - paragraph [ref=e430]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e431]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e432]:
                - generic [ref=e433]:
                  - generic [ref=e434]: alert liquidity shortage
                  - generic [ref=e435]: medium
                - paragraph [ref=e436]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e437]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e438]:
                - generic [ref=e439]:
                  - generic [ref=e440]: Unusual activity — requires review
                  - generic [ref=e441]: high
                - paragraph [ref=e442]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e443]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e444]:
                - generic [ref=e445]:
                  - generic [ref=e446]: alert liquidity shortage
                  - generic [ref=e447]: medium
                - paragraph [ref=e448]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e449]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:35" [ref=e450]:
                - generic [ref=e451]:
                  - generic [ref=e452]: Unusual activity — requires review
                  - generic [ref=e453]: high
                - paragraph [ref=e454]: anomaly · 11 Jul 2026, 19:35
            - listitem [ref=e455]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:35" [ref=e456]:
                - generic [ref=e457]:
                  - generic [ref=e458]: alert liquidity shortage
                  - generic [ref=e459]: medium
                - paragraph [ref=e460]: liquidity · 11 Jul 2026, 19:35
            - listitem [ref=e461]:
              - button "Unusual activity — requires review high anomaly · 11 Jul 2026, 19:20" [ref=e462]:
                - generic [ref=e463]:
                  - generic [ref=e464]: Unusual activity — requires review
                  - generic [ref=e465]: high
                - paragraph [ref=e466]: anomaly · 11 Jul 2026, 19:20
            - listitem [ref=e467]:
              - button "alert liquidity shortage medium liquidity · 11 Jul 2026, 19:20" [ref=e468]:
                - generic [ref=e469]:
                  - generic [ref=e470]: alert liquidity shortage
                  - generic [ref=e471]: medium
                - paragraph [ref=e472]: liquidity · 11 Jul 2026, 19:20
          - generic [ref=e474]:
            - generic [ref=e475]:
              - generic [ref=e476]:
                - generic [ref=e477]:
                  - heading "Unusual activity — requires review" [level=3] [ref=e478]
                  - paragraph [ref=e479]: anomaly · detected 11 Jul 2026, 19:58
                - generic [ref=e480]: high
              - generic [ref=e481]:
                - generic [ref=e482]: active
                - generic [ref=e483]: requires review
                - generic [ref=e484]: no case yet
              - paragraph [ref=e485]: 6 transactions of about 1000.00 BDT from 2 synthetic party(ies) on bkash within 15 minutes.
              - generic [ref=e486]: "Benign context: Repeated similar amounts are common during salary disbursement, festival demand, or recurring bill payments; this pattern is flagged only for human review and is not a determination of wrongdoing."
              - button "Open case" [ref=e488]
            - generic [ref=e489]:
              - generic [ref=e490]:
                - generic [ref=e491]:
                  - heading "Explanation" [level=3] [ref=e492]
                  - paragraph [ref=e493]: Immutable analytical narrative
                - generic [ref=e494]:
                  - button "English" [ref=e495]
                  - button "বাংলা" [ref=e496]
                  - button "Banglish" [ref=e497]
              - generic [ref=e498]:
                - generic [ref=e499]:
                  - paragraph [ref=e500]: Situation
                  - paragraph [ref=e501]: An unusual repeated-amount pattern on bKash at Demo Outlet 001 (Market) was flagged for review.
                - generic [ref=e502]:
                  - paragraph [ref=e503]: Evidence
                  - paragraph [ref=e504]: 6 transactions of about 1000.00 BDT from 2 synthetic party(ies) on bkash within 15 minutes.
                - generic [ref=e505]:
                  - paragraph [ref=e506]: Uncertainty
                  - paragraph [ref=e507]: Being flagged is not proof of wrongdoing; it indicates the pattern is unusual.
                - generic [ref=e508]:
                  - paragraph [ref=e509]: Next step
                  - paragraph [ref=e510]: Review the listed synthetic transactions before any coordination.
                - generic [ref=e511]:
                  - paragraph [ref=e512]: Benign context
                  - paragraph [ref=e513]: This may reflect normal event-driven demand.
```

# Test source

```ts
  1   | import { test, expect, Page } from "@playwright/test";
  2   | 
  3   | /**
  4   |  * Drives the thin demo UI through the MVP surfaces. Deterministic behaviour
  5   |  * (shortage / anomaly / suppression / case workflow) is asserted; exact figures
  6   |  * are left free because each run uses a fresh seed to own its data. Full case
  7   |  * lifecycle correctness (ack→note→escalate→review→resolve, immutable evidence,
  8   |  * concurrency) is proven exhaustively in the backend Phase 6 E2E suite; here we
  9   |  * confirm the same flow is reachable and rendered through the UI.
  10  |  */
  11  | 
  12  | async function loginAs(page: Page, label: string) {
  13  |   await page.goto("/");
  14  |   await page.getByRole("button", { name: label }).click();
  15  |   await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
  16  | }
  17  | 
  18  | async function runScenarioWithAnalytics(page: Page, scenarioName: string, analytics: ("liquidity" | "anomaly")[]) {
  19  |   await page.getByRole("button", { name: "Scenarios & Faults" }).click();
  20  |   const card = page.locator("section").filter({ hasText: scenarioName }).first();
  21  |   // Randomize the seed so repeated demo runs never dedup against earlier data.
  22  |   await card.locator('button[title*="Randomize"]').click();
  23  |   await card.getByRole("button", { name: "Run", exact: true }).click();
  24  |   await expect(page.getByText(/Active run/)).toBeVisible();
  25  |   await expect(page.getByText(/txns/).first()).toBeVisible();
  26  |   for (const a of analytics) {
  27  |     const btn = a === "liquidity" ? "Run liquidity analytics" : "Run anomaly analytics";
  28  |     await page.getByRole("button", { name: btn }).click();
  29  |     const log = a === "liquidity" ? /Liquidity analytics:/ : /Anomaly analytics:/;
  30  |     await expect(page.getByText(log)).toBeVisible();
  31  |   }
  32  | }
  33  | 
  34  | test("Scenario A — separated reserves and shared-cash shortage, never blended", async ({ page }) => {
  35  |   await loginAs(page, "Management");
  36  | 
  37  |   // Dashboard: shared cash + three provider cards, no blended total.
  38  |   await expect(page.getByText("Shared physical cash")).toBeVisible();
  39  |   await expect(page.getByText("bKash e-money")).toBeVisible();
  40  |   await expect(page.getByText("Nagad e-money")).toBeVisible();
  41  |   await expect(page.getByText("Rocket e-money")).toBeVisible();
  42  |   await expect(page.getByText(/never summed into a blended total/i)).toBeVisible();
  43  | 
  44  |   await runScenarioWithAnalytics(page, "Hidden Provider Shortage", ["liquidity"]);
  45  | 
  46  |   await page.getByRole("button", { name: "Liquidity", exact: true }).click();
  47  |   await expect(page.getByText("Shared physical cash")).toBeVisible();
  48  |   await expect(page.getByText(/Confidence:/).first()).toBeVisible();
  49  |   await expect(page.getByText(/Shortage/).first()).toBeVisible();
  50  | });
  51  | 
  52  | test("Scenario B & D — anomaly evidence, localized explanation, reachable case workflow", async ({ page }) => {
  53  |   await loginAs(page, "Risk Analyst");
  54  |   await runScenarioWithAnalytics(page, "Liquidity Pressure with Unusual Activity", ["anomaly"]);
  55  | 
  56  |   // Publish alertable candidates.
  57  |   await page.getByRole("button", { name: "Publish alertable candidates" }).click();
  58  |   await expect(page.getByText(/Published \d+ alert/)).toBeVisible();
  59  | 
  60  |   // Anomaly evidence: structured evidence + prominent benign context.
  61  |   await page.getByRole("button", { name: "Anomalies" }).click();
  62  |   await expect(page.getByRole("heading", { name: "near identical amounts" }).first()).toBeVisible();
  63  |   await expect(page.getByText("Plausible benign context").first()).toBeVisible();
  64  |   await expect(page.getByText("Structured evidence").first()).toBeVisible();
  65  | 
  66  |   // Alerts: select an alert, read the explanation, toggle to Bangla.
  67  |   await page.getByRole("button", { name: "Alerts", exact: true }).click();
  68  |   await page.locator("aside, div").getByRole("button").filter({ hasText: /review|Unusual|shortage/ }).first().click();
> 69  |   await expect(page.getByText("Explanation")).toBeVisible();
      |                                               ^ Error: expect(locator).toBeVisible() failed
  70  |   await page.getByRole("button", { name: "বাংলা" }).click();
  71  |   await expect(page.getByText("Situation").first()).toBeVisible();
  72  | 
  73  |   // Open (or view) the case and confirm the workflow surface renders.
  74  |   const openCase = page.getByRole("button", { name: "Open case" });
  75  |   const viewCase = page.getByRole("button", { name: "View case" });
  76  |   if (await openCase.isVisible().catch(() => false)) await openCase.click();
  77  |   else await viewCase.first().click();
  78  | 
  79  |   await expect(page.getByText("Case workflow")).toBeVisible();
  80  |   await expect(page.getByText("Recommended next step")).toBeVisible();
  81  |   await expect(page.getByText("Audit trail")).toBeVisible();
  82  | });
  83  | 
  84  | test("Scenario C — degraded data suppresses alerts (marked non-alertable)", async ({ page }) => {
  85  |   await loginAs(page, "Management");
  86  |   await runScenarioWithAnalytics(page, "Data Inconsistency", ["anomaly", "liquidity"]);
  87  | 
  88  |   await page.getByRole("button", { name: "Anomalies" }).click();
  89  |   await expect(page.getByText(/Suppressed \(degraded data\)/)).toBeVisible();
  90  |   await expect(page.getByText(/not an actionable alert/i).first()).toBeVisible();
  91  | });
  92  | 
  93  | test("Empty states render safely for a provider-scoped identity", async ({ page }) => {
  94  |   await loginAs(page, "Provider Ops — Nagad");
  95  | 
  96  |   // Deterministic right-pane empty states (independent of list contents).
  97  |   await page.getByRole("button", { name: "Cases" }).click();
  98  |   await expect(page.getByText("Select a case to manage its lifecycle.")).toBeVisible();
  99  | 
  100 |   await page.getByRole("button", { name: "Alerts", exact: true }).click();
  101 |   await expect(page.getByText(/Select an alert to view/)).toBeVisible();
  102 | });
  103 | 
```