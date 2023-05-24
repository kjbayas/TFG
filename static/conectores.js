var nodos = ('{{ nodos | safe }}');
var enlaces = ('{{ enlaces | safe }}');

console.log(nodos);
console.log(enlaces);



var svg = d3.select("#grafico")
  .append("svg")
  .attr("width", 500)
  .attr("height", 300);

svg.selectAll("line")
  .data(enlaces)
  .enter()
  .append("line")
  .attr("x1", function(d) { return d.x1; })
  .attr("y1", function(d) { return d.y1; })
  .attr("x2", function(d) { return d.x2; })
  .attr("y2", function(d) { return d.y2; })
  .style("stroke", "black");

svg.selectAll("circle")
  .data(nodos)
  .enter()
  .append("circle")
  .attr("cx", function(d) { return d.x; })
  .attr("cy", function(d) { return d.y; })
  .attr("r", 10)
  .style("fill", "blue");
