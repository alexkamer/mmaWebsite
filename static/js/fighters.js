$(document).ready(function() {
    const $searchInput = $('#fighterSearch');
    const $searchResults = $('#searchResults');
    let searchTimeout;
    let selectedFighterId = null;
    
    // Check if there's a fighter_id in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const fighterId = urlParams.get('fighter_id');
    if (fighterId) {
        loadFighterDetails(fighterId);
    }

    // Handle search input
    $searchInput.on('input', function() {
        const searchTerm = $(this).val().trim();
        
        // Clear previous timeout
        clearTimeout(searchTimeout);
        
        // Hide results if search is empty
        if (!searchTerm) {
            $searchResults.hide();
            return;
        }

        // Set new timeout for search
        searchTimeout = setTimeout(() => {
            // Fetch search results
            fetch(`/api/fighters/search?q=${encodeURIComponent(searchTerm)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length > 0) {
                        // Show results
                        $searchResults.html(
                            data.map(fighter => `
                                <div class="p-3 hover:bg-gray-100 cursor-pointer fighter-result ${fighter.id === selectedFighterId ? 'bg-gray-100' : ''}" 
                                     data-id="${fighter.id}">
                                    ${fighter.full_name}
                                </div>
                            `).join('')
                        ).show();
                    } else {
                        $searchResults.html('<div class="p-3 text-gray-500">No fighters found</div>').show();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    $searchResults.hide();
                });
        }, 300); // 300ms delay to prevent too many requests
    });

    // Handle clicking on a search result
    $searchResults.on('click', '.fighter-result', function() {
        const fighterId = $(this).data('id');
        
        // If clicking the same fighter, do nothing
        if (fighterId === selectedFighterId) {
            return;
        }
        
        // Update selected fighter
        selectedFighterId = fighterId;
        $searchInput.val($(this).text());
        $searchResults.hide();
        
        // Clear previous fighter details
        $('#fighterDetails').html('<div class="text-center p-4">Loading...</div>').removeClass('hidden');
        
        // Load new fighter details
        loadFighterDetails(fighterId);
    });

    // Clear search when clicking the input
    $searchInput.on('click', function() {
        if (selectedFighterId) {
            $(this).val('');
            selectedFighterId = null;
            $searchResults.hide();
        }
    });

    // Hide results when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('#fighterSearch, #searchResults').length) {
            $searchResults.hide();
        }
    });

    // Handle keyboard navigation
    $searchInput.on('keydown', function(e) {
        const $results = $searchResults.find('.fighter-result');
        const $selected = $results.filter('.selected');
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if ($selected.length) {
                    $selected.removeClass('selected').next().addClass('selected');
                } else {
                    $results.first().addClass('selected');
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                if ($selected.length) {
                    $selected.removeClass('selected').prev().addClass('selected');
                }
                break;
            case 'Enter':
                e.preventDefault();
                if ($selected.length) {
                    $selected.click();
                }
                break;
            case 'Escape':
                $searchResults.hide();
                break;
        }
    });

    function loadFighterDetails(fighterId) {
        // Show loading state
        $('#fighterDetails').html('<div class="text-center p-4">Loading...</div>').removeClass('hidden');
        
        // Fetch fighter details
        fetch(`/api/fighter/${fighterId}`)
            .then(response => response.json())
            .then(data => {
                // Get unique weight classes for filter
                const weightClasses = [...new Set(data.fight_history.map(fight => fight.weight_class).filter(Boolean))];
                const promotions = [...new Set(data.fight_history.map(fight => fight.league_name).filter(Boolean))];

                // Update weight class filter options
                const $weightClassFilter = $('#weightClassFilter');
                $weightClassFilter.find('option:not(:first)').remove();
                weightClasses.forEach(weightClass => {
                    $weightClassFilter.append(`<option value="${weightClass}">${weightClass}</option>`);
                });

                // Update fighter details section
                $('#fighterDetails').html(`
                    <div class="space-y-6">
                        <div class="bg-white rounded-lg shadow p-6">
                            <div class="flex items-start space-x-6">
                                ${data.headshot_url ? 
                                    `<div class="relative">
                                        ${data.flag_url ? 
                                            `<div class="absolute inset-0 bg-cover bg-center rounded-lg" style="background-image: url('${data.flag_url}');"></div>` 
                                            : ''}
                                        <img src="${data.headshot_url}" alt="${data.full_name}" class="relative w-32 h-32 object-cover rounded-lg">
                                    </div>` 
                                    : ''}
                                <div>
                                    <h2 class="text-2xl font-bold mb-2">${data.full_name}</h2>
                                    <div class="grid grid-cols-2 gap-4">
                                        <div>
                                            <p class="text-gray-600"><span class="font-semibold">Weight Class:</span> ${data.weight_class || 'N/A'}</p>
                                            <p class="text-gray-600"><span class="font-semibold">Record:</span> ${data.record || 'N/A'}</p>
                                            <p class="text-gray-600"><span class="font-semibold">Age:</span> ${data.age || 'N/A'}</p>
                                            ${data.nickname ? `<p class="text-gray-600"><span class="font-semibold">Nickname:</span> ${data.nickname}</p>` : ''}
                                        </div>
                                        <div>
                                            <p class="text-gray-600"><span class="font-semibold">Height:</span> ${data.display_height || 'N/A'}</p>
                                            <p class="text-gray-600"><span class="font-semibold">Weight:</span> ${data.display_weight || 'N/A'}</p>
                                            <p class="text-gray-600"><span class="font-semibold">Reach:</span> ${data.reach || 'N/A'}</p>
                                            ${data.association ? `<p class="text-gray-600"><span class="font-semibold">Team:</span> ${data.association}</p>` : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="bg-white rounded-lg shadow p-6">
                            <div class="flex justify-between items-center mb-4">
                                <div>
                                    <h3 class="text-xl font-bold">Fight History</h3>
                                    <div id="filteredRecord" class="text-sm text-gray-600 mt-1">
                                        Filtered Record: <span class="font-semibold">0-0-0</span>
                                        <span class="ml-4">Fights to Go the Distance: <span class="font-semibold">0/0</span></span>
                                    </div>
                                </div>
                                <div class="flex flex-col space-y-3">
                                    <div class="flex items-center space-x-4">
                                        <div class="flex items-center space-x-2">
                                            <label for="promotionFilter" class="text-sm font-medium text-gray-700 whitespace-nowrap">Promotion:</label>
                                            <select id="promotionFilter" class="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                                <option value="">All Promotions</option>
                                                ${promotions.map(promotion => `
                                                    <option value="${promotion}">${promotion}</option>
                                                `).join('')}
                                            </select>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <label for="weightClassFilter" class="text-sm font-medium text-gray-700 whitespace-nowrap">Weight Class:</label>
                                            <select id="weightClassFilter" class="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                                <option value="">All Weight Classes</option>
                                                ${weightClasses.map(weightClass => `
                                                    <option value="${weightClass}">${weightClass}</option>
                                                `).join('')}
                                            </select>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-4">
                                        ${data.fight_history.some(fight => fight.fight_title && fight.fight_title.toLowerCase().includes('title')) ? `
                                            <div class="flex items-center space-x-2">
                                                <label for="titleFightFilter" class="text-sm font-medium text-gray-700 whitespace-nowrap">Fight Type:</label>
                                                <select id="titleFightFilter" class="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                                    <option value="">All Fights</option>
                                                    <option value="title">Title Fights</option>
                                                </select>
                                            </div>
                                        ` : ''}
                                        <div class="flex items-center space-x-2">
                                            <label for="roundsFormatFilter" class="text-sm font-medium text-gray-700 whitespace-nowrap">Rounds Format:</label>
                                            <select id="roundsFormatFilter" class="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                                <option value="">All Formats</option>
                                                <option value="3">3 Rounds</option>
                                                <option value="5">5 Rounds</option>
                                            </select>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <label for="oddsFilter" class="text-sm font-medium text-gray-700 whitespace-nowrap">Odds:</label>
                                            <select id="oddsFilter" class="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
                                                <option value="">All Fights</option>
                                                <option value="favorite">Favorites</option>
                                                <option value="underdog">Underdogs</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="overflow-x-auto">
                                <table class="min-w-full">
                                    <thead>
                                        <tr class="bg-gray-50">
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Date</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Event</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Opponent</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Result</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Method</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Round</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Time</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Weight Class</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Rounds</th>
                                            <th class="px-4 py-2 text-left text-sm font-semibold text-gray-600">Odds</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-200">
                                        ${data.fight_history.map(fight => `
                                            <tr class="hover:bg-gray-50" 
                                                data-weight-class="${fight.weight_class || ''}"
                                                data-promotion="${fight.league_name || ''}"
                                                data-rounds-format="${fight.rounds_format || ''}"
                                                data-odds-type="${fight.fighter_odds ? (parseInt(fight.fighter_odds) < 0 ? 'favorite' : 'underdog') : ''}"
                                                data-result="${fight.won === null ? 'draw' : fight.won ? 'win' : 'loss'}">
                                                <td class="px-4 py-2 text-sm text-gray-900">${formatDate(fight.date)}</td>
                                                <td class="px-4 py-2 text-sm text-gray-900">
                                                    <a href="/events?event_id=${fight.event_id}" class="text-blue-600 hover:text-blue-800 hover:underline">
                                                        ${fight.event_name}
                                                    </a>
                                                </td>
                                                <td class="px-4 py-2 text-sm text-gray-900">
                                                    <a href="#" class="opponent-link text-blue-600 hover:text-blue-800 hover:underline" data-fighter-id="${fight.opponent_id}">
                                                        ${fight.opponent}
                                                    </a>
                                                </td>
                                                <td class="px-4 py-2 text-sm">
                                                    <span class="px-2 py-1 rounded-full text-xs font-semibold ${
                                                        fight.won === null ? 'bg-gray-100 text-gray-800' :
                                                        fight.won ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                    }">
                                                        ${fight.won === null ? 'Draw/NC' : fight.won ? 'Won' : 'Lost'}
                                                    </span>
                                                </td>
                                                <td class="px-4 py-2 text-sm text-gray-900">${fight.result_display_name || 'N/A'}</td>
                                                <td class="px-4 py-2 text-sm text-gray-900">${fight.end_round || 'N/A'}</td>
                                                <td class="px-4 py-2 text-sm text-gray-900">${fight.end_time || 'N/A'}</td>
                                                <td class="px-4 py-2 text-sm text-gray-900">
                                                    ${fight.weight_class || 'N/A'}
                                                    ${fight.fight_title && fight.fight_title.toLowerCase().includes('title') ? 
                                                        `<span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800" title="Title Fight">
                                                            <svg class="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                                                            </svg>
                                                            Title
                                                        </span>` 
                                                        : ''}
                                                </td>
                                                <td class="px-4 py-2 text-sm text-gray-900">${fight.rounds_format || 'N/A'}</td>
                                                <td class="px-4 py-2 text-sm text-gray-900">${fight.fighter_odds || 'N/A'}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `).removeClass('hidden');

                // Add event listener for weight class filter
                $('#promotionFilter').on('change', filterFights);
                $('#weightClassFilter').on('change', filterFights);
                $('#titleFightFilter').on('change', filterFights);
                $('#oddsFilter').on('change', filterFights);
                $('#roundsFormatFilter').on('change', filterFights);

                // Initialize the record count
                filterFights();

                function filterFights() {
                    const selectedPromotion = $('#promotionFilter').val();
                    const selectedWeightClass = $('#weightClassFilter').val();
                    const selectedFightType = $('#titleFightFilter').val();
                    const selectedOddsType = $('#oddsFilter').val();
                    const selectedRoundsFormat = $('#roundsFormatFilter').val();
                    
                    let wins = 0;
                    let losses = 0;
                    let draws = 0;
                    let distanceFights = 0;
                    let totalFights = 0;
                    
                    $('tbody tr').each(function() {
                        const rowPromotion = $(this).data('promotion');
                        const rowWeightClass = $(this).data('weight-class');
                        const isTitleFight = $(this).find('.bg-yellow-100').length > 0;
                        const rowOddsType = $(this).data('odds-type');
                        const rowRoundsFormat = $(this).data('rounds-format');
                        const result = $(this).data('result');
                        const resultText = $(this).find('td:nth-child(5)').text();
                        
                        const promotionMatch = !selectedPromotion || rowPromotion === selectedPromotion;
                        const weightClassMatch = !selectedWeightClass || rowWeightClass === selectedWeightClass;
                        const fightTypeMatch = !selectedFightType || (selectedFightType === 'title' && isTitleFight);
                        const oddsTypeMatch = !selectedOddsType || rowOddsType === selectedOddsType;
                        const roundsFormatMatch = !selectedRoundsFormat || rowRoundsFormat === parseInt(selectedRoundsFormat);
                        
                        if (promotionMatch && weightClassMatch && fightTypeMatch && oddsTypeMatch && roundsFormatMatch) {
                            $(this).show();
                            totalFights++;
                            // Count record for visible fights
                            if (result === 'win') wins++;
                            else if (result === 'loss') losses++;
                            else if (result === 'draw') draws++;
                            
                            // Check if fight went the distance by looking for 'Decision' in the Result column
                            if (resultText.includes('Decision')) {
                                distanceFights++;
                            }
                        } else {
                            $(this).hide();
                        }
                    });
                    
                    // Update the record display
                    $('#filteredRecord span').first().text(`${wins}-${losses}-${draws}`);
                    $('#filteredRecord span').last().text(`${distanceFights}/${totalFights}`);
                }

                // Add click handler for fighter names
                $(document).on('click', '.fighter-name', function(e) {
                    e.preventDefault();
                    const fighterId = $(this).data('fighter-id');
                    loadFighterDetails(fighterId);
                });

                // Add click handler for opponent links
                $(document).on('click', '.opponent-link', function(e) {
                    e.preventDefault();
                    const fighterId = $(this).data('fighter-id');
                    loadFighterDetails(fighterId);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                $('#fighterDetails').html('<div class="text-center p-4 text-red-600">Error loading fighter details</div>');
            });
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }
}); 